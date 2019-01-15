import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="HydraPMS",
    version="0.0.1.0",
    author="Christian Lachapelle",
    author_email="lachapellec@gmail.com",
    description="Hydra Proxy/Messenger Service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Devworks8/hydramessenger.git",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=["deepmerge",
                      "setuptools",
                      "PyYAML",
                      "pyzmq",
                      "tornado",
                      "cmd2",
                      "cmd2_submenu",
                      'IPython',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: Developers",
    ],
    scripts=['curve_keygen.py',
             ],
    entry_points={
        'console_scripts': ['HydraPMS=HydraPMS.hydrapms:main'],
    }
)
