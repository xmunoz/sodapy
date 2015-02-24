#!/usr/bin/env python

from setuptools import setup
execfile("sodapy/version.py")

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README').read()


kwargs = {
    "name": "sodapy",
    "version": str(__version__),
    "packages": ["sodapy"],
    "description": "Python bindings for the Socrata Open Data API",
    "long_description": long_description,
    "author": "Cristina Munoz",
    "maintainer": "Cristina Munoz",
    "author_email": "hi@xmunoz.com",
    "maintainer_email": "hi@xmunoz.com",
    "license": "Apache",
    "install_requires": ["py", "pytest", "requests"],
    "url": "https://github.com/xmunoz/sodapy",
    "download_url": "https://github.com/xmunoz/sodapy/archive/master.tar.gz",
    "keywords": "soda socrata opendata api",
    "classifiers": [
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
}

setup(**kwargs)
