from setuptools import setup

setup(
    name = "pyGUMarket",
    version = "1.0.0",
    author = "SaltBlocks",
    description = ("A command line utility for trading on Immutable X written in python."),
    url = "https://github.com/SaltBlocks/py-gods-unchained-market",
    packages=['IMXlib.py', 'key_loader.py', "pyGUMarket.py"],
)