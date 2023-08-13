# py-gods-unchained-market

A command line Gods Unchained marketplace written in python.\
Supports buying, selling and transfering GU cards as well as creating new wallets and linking them to the Immutable X platform.

## Notice
On september 1st 2023, the old IMX V1 orders API will cease to service requests. Old versions of IMXlib will stop functioning at this time. [py-gods-unchained-market v2.0](https://github.com/SaltBlocks/py-gods-unchained-market/releases/tag/v2.0) is updated to use the new API endpoints and will still work after this date. Older versions however will become unusable at this time.

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
You'll be asked to either import a wallet using the private key, link to a web wallet (i.e. metamask) or generate a new wallet. Wallets are password protected using AES256 encryption with PBKDF2 for key generation. Check [key_loader.py](https://github.com/SaltBlocks/py-gods-unchained-market/blob/main/key_loader.py) to see how this is implemented. Web wallets use the security features offered by the web wallet. After loading a wallet you'll be shown its current balance and you'll be able to search the market for Gods Unchained cards to either buy, sell or transfer.