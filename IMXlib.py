from ctypes import CDLL, create_string_buffer, Structure, c_char, c_char_p, c_int, c_ulonglong, c_double, addressof
import platform
import os
import json

arch = "Win32"

if "64" in platform.architecture()[0]:
    arch = "x64"

dllname = "IMXlib.dll"
dllpath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + arch + os.path.sep + dllname
imx_lib = CDLL(dllpath)

'''
Structures used to pass lists of specific data to IMXlib.
'''

class FEE(Structure):
    ''' Structure for Fees that can be passed to IMXlib

    Parameters
    ----------
    address : byte string
        The address that the fee should be transfered to in the form of a hex-string (0x......).
    percentage : int
        The percentate of the base price that should be added as fee.
    '''
    _fields_ = [("address", c_char * 43), 
             ("percentage", c_int)]

class NFT(Structure):
    ''' Structure for NFTs that can be passed to IMXlib

    Parameters
    ----------
    token_address : byte string
        The address of the collection the NFT is a part of in the form of a hex-string (0x......).
    token_id : unsigned long long
        The id of the NFT.
    '''
    _fields_ = [("token_address", c_char * 43),
             ("token_id", c_ulonglong)]

'''
General functions for generating eth addresses and signing messages.
'''

def eth_generate_key():
    ''' Generates a random ethereum private key.

    Returns
    ----------
    int : The private key as an integer.
    '''
    res = create_string_buffer(67)
    imx_lib.eth_generate_key(res, 67)
    return int(res.value.decode(), 16)

def eth_get_address(eth_key):
    ''' Calculates the Ethereum address associated with the provided private key.
    
    Parameters
    ----------
    eth_key : int
        The private key for which to calculate the address. Can also be provided as a hex string (0x......).

    Returns
    ----------
    int : The address associated with the pricate key as an integer.
    '''
    res = create_string_buffer(43)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    imx_lib.eth_get_address(eth_key.encode("utf-8"), res, 43)
    return int(res.value.decode(), 16)

def eth_sign_message(message: str, eth_key):
    ''' Sign the provided message with the provided private key.

    Parameters
    ----------
    message : str
        The message to sign
    eth_key : int
        The private key with which to sign the message. Can also be provided as a hex string (0x......).
    
    Returns
    ----------
    int : The signature of the message signed with the private key as an integer.
    '''
    res = create_string_buffer(133)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    imx_lib.eth_sign_message(message.encode("utf-8"), eth_key.encode("utf-8"), res, 133)
    return int(res.value.decode(), 16)

'''
Functions for interacting with IMX that require access to the ethereum private key.
'''

def imx_register_address(eth_key):
    ''' Sets up the immutable X key for the provided ethereum private key.
    
    Parameters
    ----------
    eth_key : int
        The private key of the wallet to register with IMX. Can also be provided as a hex string (0x......).
    
    Returns
    ----------
    str : The response from the server after attempting to register the wallet.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    imx_lib.imx_register_address(eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_sell_nft(nft_address, nft_id, token_id, price: float, fees, eth_key):
    ''' Creates a sell order for an nft on the Immutable X marketplace

    Parameters
    ----------
    nft_address : int
        The address of the collection the nft is part of. Can also be provided as a hex string (0x......).
    nft_id : int
        The id of the nft to sell.
    token_id : str
        The id of the token for which to sell the nft.
    price : float
        The price for which to sell.
    fees : array
        An array of fees to add to the sale.
    eth_key : int
        The private key of the wallet that owns the nft to sell. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server after attempting to create the sell order.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    if isinstance(nft_address, int):
        nft_address = str(hex(nft_address))
    if isinstance(nft_id, int):
        nft_id = str(nft_id)
    if isinstance(token_id, int):
        token_id = str(hex(token_id))
    imx_lib.imx_sell_nft(nft_address.encode("utf-8"), nft_id.encode("utf-8"), token_id.encode("utf-8"), c_double(price), 
                      (FEE * len(fees))(*fees), len(fees), eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_offer_nft(nft_address, nft_id, token_id, price: float, fees, eth_key):
    ''' Creates a buy offer for an nft on the Immutable X marketplace

    Parameters
    ----------
    nft_address : int
        The address of the collection the nft is part of. Can also be provided as a hex string (0x......).
    nft_id : int
        The id of the nft to sell.
    token_id : str
        The id of the token for which to buy the nft.
    price : float
        The price for which to buy.
    fees : array
        An array of fees to add to the sale.
    eth_key : int
        The private key of the wallet that owns the nft to sell. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server after attempting to create the offer.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    if isinstance(nft_address, int):
        nft_address = str(hex(nft_address))
    if isinstance(nft_id, int):
        nft_id = str(nft_id)
    if isinstance(token_id, int):
        token_id = str(hex(token_id))
    imx_lib.imx_offer_nft(nft_address.encode("utf-8"), nft_id.encode("utf-8"), token_id.encode("utf-8"), c_double(price), 
                       (FEE * len(fees))(*fees), len(fees), eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_cancel_order(order_id, eth_key):
    ''' Creates a cancel order for an nft on the Immutable X marketplace

    Parameters
    ----------
    order_id : int
        The id of the order to cancel.
    eth_key : int
        The private key of the wallet that created the order. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server after attempting to cancel the order.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    if isinstance(order_id, int):
        order_id = str(order_id)
    imx_lib.imx_cancel_order(order_id.encode("utf-8"), eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_transfer_nft(nft_address, nft_id, receiver_address, eth_key):
    ''' Transfers an nft to a different wallet on Immutable X.

    Parameters
    ----------
    nft_address : int
        The address of the collection the nft is part of.
    nft_id : int
        The id of the nft to transfer.
    receiver_address : int
        The address to send the nft to. Can also be provided as a hex string (0x.....).
    eth_key : int
        The private key of the wallet creating the transfer. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server after attempting to transfer the nft.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    if isinstance(nft_address, int):
        nft_address = str(hex(nft_address))
    if isinstance(nft_id, int):
        nft_id = str(nft_id)
    if isinstance(receiver_address, int):
        receiver_address = str(hex(receiver_address))
    imx_lib.imx_transfer_nft(nft_address.encode("utf-8"), nft_id.encode("utf-8"), receiver_address.encode("utf-8"), eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_transfer_nfts(nft_list, receiver_address, eth_key):
    ''' Transfers an nft to a different wallet on Immutable X.

    Parameters
    ----------
    nft_list : list of NFT
        List of NFTs to be transfered.
    receiver_address : int
        The address to send the nfts to. Can also be provided as a hex string (0x.....).
    eth_key : int
        The private key of the wallet creating the transfer. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server after attempting to transfer the nfts.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    if isinstance(receiver_address, int):
        receiver_address = str(hex(receiver_address))
    imx_lib.imx_transfer_nfts((NFT * len(nft_list))(*nft_list), len(nft_list), receiver_address.encode("utf-8"), eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_transfer_token(token_id, amount: float, receiver_address, eth_key):
    ''' Transfers the specified amount of a token to a different wallet on Immutable X.

    Parameters
    ----------
    token_id : int
        The address of the token to send or "ETH" for ethereum.
    amount : float
        The amount of the token to send.
    receiver_address : int
        The address to send the tokens to. Can also be provided as a hex string (0x.....).
    eth_key : int
        The private key of the wallet creating the transfer. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server after attempting to transfer the nft.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    if isinstance(token_id, int):
        token_id = str(hex(token_id))
    if isinstance(receiver_address, int):
        receiver_address = str(hex(receiver_address))
    imx_lib.imx_transfer_token(token_id.encode("utf-8"), c_double(amount), receiver_address.encode("utf-8"), eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_buy_nft(order_id, price : float, fees, eth_key):
    ''' Buy the order specified on Immutable X (includes a 1% taker marketplace fee by default). Can also be used to accept a buy offer.

    Parameters
    ----------
    order_id : int
        The id for the order that should be bought.
    price : float
        The price that should be spent buying the order (including all fees). This should exceed the price of the order or the buy order will be rejected.
    fees : array
        An array of fees to add to the sale.
    eth_key : int
        The private key of the wallet used to buy the order. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server after attempting to transfer the nft.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_key, int):
        eth_key = str(hex(eth_key))
    if isinstance(order_id, int):
        order_id = str(order_id)
    imx_lib.imx_buy_nft(order_id.encode("utf-8"), c_double(price), 
                      (FEE * len(fees))(*fees), len(fees), eth_key.encode("utf-8"), res, 1000)
    return res.value.decode()

'''
Functions that don't require the ethereum private key to IMXlib.
These functions can be used to execute trades using a hardware wallet.
'''

def imx_get_token_trade_fee(nft_address, nft_id):
    ''' Get the buyer trade fee on a specific asset when trading it on Immutable X (excludes the taker marketplace fee, usually 1%).

    Parameters
    ----------
    nft_address : int
        The address of the collection the nft is part of. Can also be provided as a hex string (0x......).
    nft_id : int
        The id of the nft to get the fee for.

    Returns
    ----------
    str : The response from the server after attempting to transfer the nft.
    '''
    if isinstance(nft_address, int):
        nft_address = str(hex(nft_address))
    if isinstance(nft_id, int):
        nft_id = str(nft_id)
    return imx_lib.imx_get_token_trade_fee(nft_address.encode("utf-8"), nft_id.encode("utf-8"), None)

def imx_register_address_presign(eth_address, imx_seed_sig, imx_link_sig):
    ''' Sets up the immutable X key for the provided ethereum private key.
    
    Parameters
    ----------
    eth_address : int
        The address of the wallet to register with IMX. Can also be provided as a hex string (0x......).
    imx_seed_sig : int
        The signature of the message imx_seed_msg ("Only sign this request ...") signed by the users ETH wallet.
    imx_link_sig : int
        The signature of the imx_link_msg ("Only sign this key linking request from Immutable X") signed by the users ETH wallet.
    Returns
    ----------
    str : The response from the server after attempting to register the wallet.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_address, int):
        eth_address = str(hex(eth_address))
    if isinstance(imx_seed_sig, int):
        imx_seed_sig = str(hex(imx_seed_sig))
    if isinstance(imx_link_sig, int):
        imx_link_sig = str(hex(imx_link_sig))
    imx_lib.imx_register_address_presigned(eth_address.encode("utf-8"), imx_link_sig.encode("utf-8"), imx_seed_sig.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_request_cancel_order(order_id):
    ''' Fetches the message that needs to be signed by the user in order to be able to cancel the given order.
    
    Parameters
    ----------
    order_id : int
        The ID of the order to cancel.
    Returns
    ----------
    str : The message the needs to be signed to cancel the order.
    '''
    if isinstance(order_id, int):
        order_id = str(order_id)
    res = create_string_buffer(1000)
    imx_lib.imx_request_cancel_order(order_id.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_finish_cancel_order(order_id, eth_address, imx_seed_sig, imx_transaction_sig):
    ''' Attempts to cancel the given order using the message signature provided.
    
    Parameters
    ----------
    order_id : int
        The ID of the order to cancel.
    eth_address : int
        The address of the user trying to cancel the order.
    imx_seed_sig : int
        The signature of the message imx_seed_msg ("Only sign this request ...") signed by the users ETH wallet.
    imx_transaction_sig : int
        The signature of the message returned by the imx_request_cancel_order method signed by the users ETH wallet.
    Returns
    ----------
    str : The response from the server after attempting to cancel the order.
    '''
    if isinstance(order_id, int):
        order_id = str(order_id)
    if isinstance(eth_address, int):
        eth_address = str(hex(eth_address))
    if isinstance(imx_seed_sig, int):
        imx_seed_sig = str(hex(imx_seed_sig))
    if isinstance(imx_transaction_sig, int):
        imx_transaction_sig = str(hex(imx_transaction_sig))
    res = create_string_buffer(1000)
    imx_lib.imx_finish_cancel_order(order_id.encode("utf-8"), eth_address.encode("utf-8"), imx_seed_sig.encode("utf-8"), imx_transaction_sig.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_request_sell_nft(nft_address, nft_id, token_id, price, fees, seller_address):
    ''' Requests a signable sell order for an nft on the Immutable X marketplace

    Parameters
    ----------
    nft_address : int
        The address of the collection the nft is part of. Can also be provided as a hex string (0x......).
    nft_id : int
        The id of the nft to sell.
    token_id : str
        The id of the token for which to sell the nft (or "ETH" for ethereum).
    price : float
        The price for which to sell.
    fees : array
        An array of fees to add to the sale.
    seller_address : int
        The address of the wallet that owns the nft to sell. Can also be provided as a hex string (0x......).

    Returns
    ----------
    str : The response from the server. If the request succeeded, this will contain a nonce and a message that needs to be signed to submit the sell order.
    '''
    res = create_string_buffer(1000)
    if isinstance(nft_address, int):
        nft_address = str(hex(nft_address))
    if isinstance(nft_id, int):
        nft_id = str(nft_id)
    if isinstance(token_id, int):
        token_id = str(hex(token_id))
    if isinstance(seller_address, int):
        seller_address = str(hex(seller_address))
    imx_lib.imx_request_sell_nft(nft_address.encode("utf-8"), nft_id.encode("utf-8"), token_id.encode("utf-8"), c_double(price), 
                      (FEE * len(fees))(*fees), len(fees), seller_address.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_finish_sell_or_offer_nft(nonce, imx_seed_sig, imx_transaction_sig):
    ''' Submit a previously signed sell/offer order for an nft to the Immutable X marketplace

    Parameters
    ----------
    nonce : int
        The nonce of the order to submit, this is returned by imx_request_sell_nft.
    imx_seed_sig : int
        The signature of the message imx_seed_msg ("Only sign this request ...") signed by the users ETH wallet.
    imx_transaction_sig : int
        The signature of the message returned by the imx_request_cancel_order method signed by the users ETH wallet.

    Returns
    ----------
    str : The response from the server after attempting to create the sell/offer order.
    '''
    if isinstance(nonce, int):
        nonce = str(nonce)
    if isinstance(imx_seed_sig, int):
        imx_seed_sig = str(hex(imx_seed_sig))
    if isinstance(imx_transaction_sig, int):
        imx_transaction_sig = str(hex(imx_transaction_sig))
    res = create_string_buffer(1000)
    imx_lib.imx_finish_sell_or_offer_nft(nonce.encode("utf-8"), imx_seed_sig.encode("utf-8"), imx_transaction_sig.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_request_buy_nft(order_id, eth_address, fees):
    ''' Requests a signable buy order for an order on the Immutable X marketplace. Can also be used to accept a buy offer.

    Parameters
    ----------
    order_id : int
        The ID of the order you're trying to buy.
    eth_address : int
        The eth address of the user trying to buy the order.
    fees : array
        An array of fees to add to the sale.

    Returns
    ----------
    str : The response from the server. If the request succeeded, this will contain a nonce and a message that needs to be signed to submit the buy order.
    '''
    res = create_string_buffer(1000)
    if isinstance(eth_address, int):
        eth_address = str(hex(eth_address))
    if isinstance(order_id, int):
        order_id = str(order_id)
    imx_lib.imx_request_buy_nft(order_id.encode("utf-8"), eth_address.encode("utf-8"), (FEE * len(fees))(*fees), len(fees), res, 1000)
    return res.value.decode()

def imx_finish_buy_nft(nonce, price_limit: float, imx_seed_sig, imx_transaction_sig):
    ''' Submit a previously signed buy order to the Immutable X marketplace. Can also be used to accept a buy offer.

    Parameters
    ----------
    nonce : int
        The nonce of the order to submit, this is returned by imx_request_buy_nft.
    price_limit : float
        Maximum amount to spend buying the order.
    imx_seed_sig : int
        The signature of the message imx_seed_msg ("Only sign this request ...") signed by the users ETH wallet.
    imx_transaction_sig : int
        The signature of the message returned by the imx_request_buy_nft method signed by the users ETH wallet.

    Returns
    ----------
    str : The response from the server after attempting to buy the specified order.
    '''
    res = create_string_buffer(1000)
    if isinstance(nonce, int):
        nonce = str(nonce)
    if isinstance(imx_seed_sig, int):
        imx_seed_sig = str(hex(imx_seed_sig))
    if isinstance(imx_transaction_sig, int):
        imx_transaction_sig = str(hex(imx_transaction_sig))
    imx_lib.imx_finish_buy_nft(nonce.encode("utf-8"), c_double(price_limit), imx_seed_sig.encode("utf-8"), imx_transaction_sig.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_request_transfer_nft(nft_address, nft_id, receiver_address, sender_address):
    ''' Requests a signable transfer order on the Immutable X marketplace.

    Parameters
    ----------
    nft_address : int
        The address of the collection the nft to transfer is part of.
    nft_id : int
        The id of the nft to transfer.
    receiver_address : int
        The address of the wallet the nft will be sent to.
    sender_address : int
        The address of the wallet the nft will be sent from.

    Returns
    ----------
    str : The response from the server. If the request succeeded, this will contain a nonce and a message that needs to be signed to submit the transfer order.
    '''
    res = create_string_buffer(1000)
    if isinstance(nft_address, int):
        nft_address = str(hex(nft_address))
    if isinstance(nft_id, int):
        nft_id = str(nft_id)
    if isinstance(receiver_address, int):
        receiver_address = str(hex(receiver_address))
    if isinstance(sender_address, int):
        sender_address = str(hex(sender_address))
    imx_lib.imx_request_transfer_nft(nft_address.encode("utf-8"), nft_id.encode("utf-8"), receiver_address.encode("utf-8"), sender_address.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_request_transfer_token(token_id, amount: float, receiver_address, sender_address):
    ''' Requests a signable transfer order on the Immutable X marketplace.

    Parameters
    ----------
    nft_address : int
        The address of the collection the nft to transfer is part of.
    nft_id : int
        The id of the nft to transfer.
    receiver_address : int
        The address of the wallet the nft will be sent to.
    sender_address : int
        The address of the wallet the nft will be sent from.

    Returns
    ----------
    str : The response from the server. If the request succeeded, this will contain a nonce and a message that needs to be signed to submit the transfer order.
    '''
    res = create_string_buffer(1000)
    if isinstance(token_id, int):
        token_id = str(hex(token_id))
    if isinstance(receiver_address, int):
        receiver_address = str(hex(receiver_address))
    if isinstance(sender_address, int):
        sender_address = str(hex(sender_address))
    imx_lib.imx_request_transfer_token(token_id.encode("utf-8"), c_double(amount), receiver_address.encode("utf-8"), sender_address.encode("utf-8"), res, 1000)
    return res.value.decode()
    

def imx_finish_transfer(nonce, imx_seed_sig, imx_transaction_sig):
    ''' Submit a previously signed transfer order to the Immutable X marketplace.

    Parameters
    ----------
    nonce : int
        The nonce of the order to submit, this is returned by imx_request_transfer_nft or imx_request_transfer_token.
    imx_seed_sig : int
        The signature of the message imx_seed_msg ("Only sign this request ...") signed by the users ETH wallet.
    imx_transaction_sig : int
        The signature of the message returned by the imx_request_transfer_nft or imx_request_transfer_token method signed by the users ETH wallet.

    Returns
    ----------
    str : The response from the server after attempting to execute the specified transfer order.
    '''
    if isinstance(nonce, int):
        nonce = str(nonce)
    if isinstance(imx_seed_sig, int):
        imx_seed_sig = str(hex(imx_seed_sig))
    if isinstance(imx_transaction_sig, int):
        imx_transaction_sig = str(hex(imx_transaction_sig))
    res = create_string_buffer(1000)
    imx_lib.imx_finish_transfer(nonce.encode("utf-8"), imx_seed_sig.encode("utf-8"), imx_transaction_sig.encode("utf-8"), res, 1000)
    return res.value.decode()

def imx_get_seed_msg():
    ''' Gets the IMX seed message that needs to be signed to perform actions on the IMX platform.
    
     Returns
    ----------
    str : The imx seed string.
    '''
    return c_to_string(imx_lib.imx_seed_message)

def imx_get_link_msg():
    ''' Gets the IMX link message that needs to be signed to link an ethereum wallet to the IMX platform.
    
     Returns
    ----------
    str : The imx link string.
    '''
    return c_to_string(imx_lib.imx_link_message)

def c_to_string(c_var):
    ''' Retrieves a string from IMXlib using a pointer. '''
    return c_char_p.from_address(addressof(c_var)).value.decode()

def main():
    ''' Example that generates a new wallet and links it to the IMX platform using the automatic and manual methods. '''
    # Generate a new wallet and link it ot IMX letting IMXlib handle all the signing.
    print(f"--- Automatic ---")
    eth_key = eth_generate_key()
    print(f"PRIVATE_KEY: {hex(eth_key)}")
    address = eth_get_address(eth_key)
    print(f"ADDRESS: {hex(address)}")
    link_result = imx_register_address(eth_key)
    if "tx_hash" in link_result:
        print(f"Successfully linked wallet with address {hex(address)} to the IMX platform.")
    else:
        print(f"Failed to link wallet with address {hex(address)} to the IMX platform.\nERROR: {link_result}")
    
    # Generate a new wallet and link it ot IMX manually requesting the required signatures (usefull in case the private key cannot be accessed like with a hardware wallet).
    print(f"\n\n\n--- Manual ---")
    eth_key = eth_generate_key()
    print(f"PRIVATE_KEY: {hex(eth_key)}")
    address = eth_get_address(eth_key)
    print(f"ADDRESS: {hex(address)}")
    imx_seed_msg = imx_get_seed_msg()
    imx_seed_sig = eth_sign_message(imx_seed_msg, eth_key)
    print(f"IMX_SEED: {imx_seed_msg}\nIMX_SEED_SIGNATURE: {hex(imx_seed_sig)}")
    imx_link_msg = imx_get_link_msg()
    imx_link_sig = eth_sign_message(imx_link_msg, eth_key)
    print(f"IMX_LINK: {imx_link_msg}\nIMX_LINK_SIGNATURE: {hex(imx_link_sig)}")
    link_result = imx_register_address_presign(address, imx_seed_sig, imx_link_sig)
    if "tx_hash" in link_result:
        print(f"Successfully linked wallet with address {hex(address)} to the IMX platform.")
    else:
        print(f"Failed to link wallet with address {hex(address)} to the IMX platform.\nERROR: {link_result}")
    

if __name__ == "__main__":
    main()