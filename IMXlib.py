from ctypes import CDLL, create_string_buffer, Structure, c_char, c_char_p, c_int, c_ulonglong, c_double, addressof
import platform
import os

arch = "Win32"

if "64" in platform.architecture()[0]:
	arch = "x64"

dllname = "IMXlib.dll"
dllpath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + arch + os.path.sep + dllname
imx_lib = CDLL(dllpath)

class FEE(Structure):
	''' Structure for Fees that can be passed to IMX

	Parameters
	----------
	address : byte string
		The address that the fee should be transfered to in the form of a hex-string (0x......).
	percentage : int
		The percentate of the base price that should be added as fee.
	'''
	_fields_ = [("address", c_char * 43), 
			 ("percentage", c_int)]

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
	str : The response from the server after attempting to cancel the order.
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

def imx_tranfer_token(token_id, amount: float, receiver_address, eth_key):
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

def imx_get_token_trade_fee(nft_address, nft_id):
	''' Get the trade fee on a specific asset when trading it on Immutable X (includes a 1% maker marketplace fee, excluding taker marketplace fee).

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

def imx_buy_nft(order_id : int, nft_address, nft_id, token_id, price : float, fees, eth_key):
	''' Buy the order specified on Immutable X (includes a 1% taker marketplace fee by default).

	Parameters
	----------
	order_id : int
		The id for the order that should be bought.
	nft_address : int
		The address of the collection the nft is part of. Can also be provided as a hex string (0x......).
	nft_id : int
		The id of the nft to get the fee for.
	token_id : int
		The id for the token to use to buy the order, or ETH for ethereum. Can also be provided as a hex string (0x......).
	price : float
		The price that should be spent buying the order (including all fees). This should match the price of the order or the buy order will be rejected.
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
	if isinstance(nft_address, int):
		nft_address = str(hex(nft_address))
	if isinstance(nft_id, int):
		nft_id = str(nft_id)
	if isinstance(token_id, int):
		token_id = str(hex(token_id))
	imx_lib.imx_buy_nft(c_ulonglong(order_id), nft_address.encode("utf-8"), nft_id.encode("utf-8"), token_id.encode("utf-8"), c_double(price), 
					  (FEE * len(fees))(*fees), len(fees), eth_key.encode("utf-8"), res, 1000)
	return res.value.decode()

def c_to_string(c_var):
	return c_char_p.from_address(addressof(c_var)).value.decode()

def main():
	eth_key = eth_generate_key()
	address = eth_get_address(eth_key)
	print(f"ADDRESS: {hex(address)}")

	#nft_address = 0xacb3c6a43d15b907e8433077b6d38ae40936fe2c
	#nft_id = 209512341
	#price = 1
	#fee = FEE(b"0x216df17ec98bae6047f2c5466162333f1aee23dc", 25)
	#print(imx_sell_nft(nft_address, nft_id, "ETH", price, [fee], eth_key))
	
	#amount = 0.0000001
	#receiver = 0x926268e740a64d9efa377a26553fd522dc70c053
	#print(imx_tranfer_token("ETH", amount, receiver, eth_key))
	#print(imx_transfer_nft(nft_address, nft_id, receiver, eth_key))
	#print(imx_get_token_trade_fee(nft_address, nft_id))
	#print(imx_register_address(eth_generate_key()))
	#order_id = 244755386
	#print(imx_cancel_order(order_id, eth_key))


if __name__ == "__main__":
	main()