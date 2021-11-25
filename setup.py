#!/usr/bin/env python3

from distutils.core import setup
from distutils.cmd import Command


setup(
    name="dht",
    version="1.0",
    url="https://github.com/shizacat/dht-pi-python",
    author="Matveev Alexey",
    description="",
    packages=["dht", ],
    install_requires=["RPi.GPIO"],
)
