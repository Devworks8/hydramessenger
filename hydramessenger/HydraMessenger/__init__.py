from argparse import ArgumentParser
from multiprocessing import Process
from random import randint
import os
from datetime import datetime, timedelta
import signal
import zmq
from zmq.auth.asyncio import AsyncioAuthenticator
from zmq.eventloop.zmqstream import ZMQStream


from hydramessenger.HydraMessenger.configure import CfgManager
from hydramessenger.HydraMessenger.MessageHeaders.msg_command import *
from hydramessenger.HydraMessenger.Utils.key_monkey import *


class HydraProxy(Process):
    def __init__(self, frontend_port=None, backend_port=None):
        super().__init__()
        self.settings = CfgManager()

        self.frontend_host = self.settings.get(header='service_proxy_frontend_host')[1]
        self.backend_host = self.settings.get(header='service_proxy_backend_host')[1]

        self.frontend_port = self.settings.get(header='service_proxy_frontend_port')[1]
        self.backend_port = self.settings.get(header='service_proxy_backend_port')[1]

        # crypto = True means 'use CurveZMQ'. False means don't.
        self.frontend_crypto = self.settings.get('service_proxy_frontend_crypto')[1]
        self.backend_crypto = self.settings.get('service_proxy_backend_crypto')[1]

        # zap_auth = True means 'use ZAP'. This will restrict connections to clients whose public keys are in
        # the ~/.curve/authorized-clients/ directory. Set this to false to allow any client with the server's
        # public key to connect, without requiring the server to possess each client's public key.
        self.frontend_zap_auth = self.settings.get('service_proxy_frontend_zap')[1]
        self.backend_zap_auth = self.settings.get('service_proxy_backend_zap')[1]

        self.frontend_identities = {}
        self.backend_identities = {}

    def run(self):
        context = zmq.Context()
        # Socket facing clients
        frontend = context.socket(zmq.XREP)

        # Setup crypto:
        if self.frontend_crypto:
            keymonkey = KeyMonkey("HydraProxyFrontend")
            frontend = keymonkey.setupServer(frontend, "tcp://{host}:{port}".format(host=self.frontend_host,
                                                                                    port=self.frontend_port))

        # :FIXME Need to finish frontend ZAP implementation
        # Setup ZAP:
        """
        if self.zap_auth:
            if not self.crypto:
                print("ZAP requires CurveZMQ (crypto) to be enabled. Exiting.")
                sys.exit(1)

            auth = AsyncioAuthenticator(context)
            # FIXME: Need to supply a list of address' to deny.
            auth.deny([''])
            print("ZAP enabled.\nAuthorizing clients in %s." % keymonkey.authorized_clients_dir)
            auth.configure_curve(domain='*', location=keymonkey.authorized_clients_dir)
            auth.start()
        """

        frontend.bind("tcp://{host}:{port}".format(host=self.frontend_host,
                                                   port=self.frontend_port))

        # Socket facing servers
        backend = context.socket(zmq.XREQ)

        # Setup crypto:
        if self.backend_crypto:
            keymonkey = KeyMonkey("HydraProxyBackend")
            backend = keymonkey.setupServer(backend, "tcp://{host}:{port}".format(host=self.backend_host,
                                                                                  port=self.backend_port))

        # :FIXME Need to finish backend ZAP implementation
        # Setup ZAP:
        """
        if self.zap_auth:
            if not self.crypto:
                print("ZAP requires CurveZMQ (crypto) to be enabled. Exiting.")
                sys.exit(1)

            auth = AsyncioAuthenticator(context)
            # FIXME: Need to supply a list of address' to deny.
            auth.deny([''])
            print("ZAP enabled.\nAuthorizing clients in %s." % keymonkey.authorized_clients_dir)
            auth.configure_curve(domain='*', location=keymonkey.authorized_clients_dir)
            auth.start()
        """

        backend.bind("tcp://{host}:{port}".format(host=self.backend_host,
                                                  port=self.backend_port))

        print("Proxy starting up\n")

        try:
            zmq.proxy(frontend, backend)
            print("Proxy started")

        except Exception as e:
            print("ERROR: Proxy failed to start. : {}".format(e))
            exit(1)


class HydraMessenger(Process):
    def __init__(self, server=None, backend_port=None):
        super().__init__()
        self.settings = CfgManager()
        self.command_message = CommandMessage()
        self.identity = "%04X-%04X" % (randint(0, 0x10000), randint(0, 0x10000))
        self.backend_host = self.settings.get('service_proxy_backend_host')[1]
        self.backend_port = self.settings.get('service_proxy_backend_port')[1]
        self.crypto = self.settings.get('service_messenger_crypto')[1]

    def run(self):
        context = zmq.Context()
        worker = context.socket(zmq.REP)

        # setup crypto
        if self.crypto:
            keymonkey = KeyMonkey("HydraMessenger")
            worker = keymonkey.setupClient(worker, "tcp://{host}:{port}".format(host=self.backend_host,
                                                                                port=self.backend_port),
                                           "HydraProxyBackend")

        worker.connect("tcp://{host}:{port}".format(host=self.backend_host, port=self.backend_port))

        results = MessengerWorker(worker.recv_multipart())
        worker.send_multipart(results)
        print("Worker %s sending results" % self.identity)
        print(results)


class MessengerWorker:
    def __init__(self, msg):
        self.message = msg

    def check_message(self, msg):
        return msg


processes = []


def signal_handler(_signum, _frame):
    for process in processes:
        if process.is_alive():
            os.kill(process.pid, signal.SIGKILL)

    for process in processes:
        process.join()


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Args parsing
    """
    parser = ArgumentParser(description='Hydra Proxy and Messenger services.')
    parser.add_argument('procs', type=int,
                        help='Number of message workers to use.')
    parser.add_argument('proxy',
                        help='Proxy server address.')
    parser.add_argument('frontend_port',
                        help='Frontend proxy port for clients to connect to.')
    parser.add_argument('backend_port',
                        help='Backend proxy port for workers to connect to.')

    args = parser.parse_args()

    if args:
        frontend_port = args.frontend_port
        backend_port = args.backend_port
    else:
        frontend_port = None
        backend_port = None

    """

    proxy_proc = HydraProxy()
    proxy_proc.start()
    processes.append(proxy_proc)

    messenger_proc = HydraMessenger()
    messenger_proc.start()
    processes.append(messenger_proc)


if __name__ == '__main__':
    main()