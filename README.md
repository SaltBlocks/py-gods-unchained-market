# py-gods-unchained-market

A command line Gods Unchained marketplace written in python.\
Supports buying, selling and transfering GU cards as well as creating new wallets and linking them to the Immutable X platform.



## Installation

This project uses [pycryptodome](https://pypi.org/project/pycryptodome/) and [requests](https://pypi.org/project/requests/). These requirements can be installed using the package manager [pip](https://pip.pypa.io/en/stable/).\
Requirements for this project can be installed by running:

```bash
pip install -r requirements.txt
```

## Usage
Run 'pyGUMarket.py' to start the application.
```bash
python pyGUMarket.py
```
You'll be asked to either import a wallet using the private key or generate a new wallet. Wallets are password protected using AES256 encryption with PBKDF2 for key generation. Check [key_loader.py](https://github.com/SaltBlocks/py-gods-unchained-market/blob/main/key_loader.py) to see how this is implemented. After loading a wallet you'll be shown its current balance and you'll be able to search the market for Gods Unchained cards to either buy, sell or transfer.