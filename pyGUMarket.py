''' Python Command line utility for trading Gods Unchained cards on the Immutable X platform.

This is mostly intended as a testing/example program for the IMXlib library.
Keys are securely stored using AES256 encryption. The key storing mechanism is implemented in key_loader.py.

Functions for interacting with Immutable X are implemented in IMXlib.py.
'''

from key_loader import prompt_load_wallet
from IMXlib import eth_get_address, imx_register_address, imx_get_token_trade_fee, imx_sell_nft, imx_buy_nft, imx_transfer_nft, imx_tranfer_token, imx_cancel_order, FEE
from requests import request
from urllib.parse import quote
import json
import time

def call_retry(function, *args):
	''' Used for automatically repeating failed network calls. Will wait three seconds to try again if the provided method call returns an error.

	Parameters
	----------
	function
		The function that should be called.
	args
		The arguments to call the function with.

	Returns
	----------
	The return value of the function call.
	'''
	while True:
		try:
			result = function(*args)
			break
		except:
			print("Error during network call, waiting 3 seconds to try again...")
			time.sleep(3)
	return result

def get_eth_price():
	''' Fetches the current price of ETH in USD.

	Returns
	----------
	float : The current price of ETH in USD. 
	'''
	return json.loads(call_retry(request, "GET", "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd").content)["ethereum"]["usd"]

def is_linked(address : int):
	''' Checks if the provided address is linked to IMX.

	Parameters
	----------
	address : int
		The address of the wallet to check link status for.

	Returns
	----------
	bool : True if the wallet is linked, False if it is not.
	'''
	url = f"https://api.x.immutable.com/v1/users/{hex(address)}"
	link_data = call_retry(request, "GET", url).text
	return not "Account not found" in link_data

def link_wallet(address, eth_priv):
	''' Make sure the wallet is linked to IMX, if it isn't, ask to set it up for the user.
		Unless you've never connected this wallet to IMX before, this should already be done.

	Parameters
	----------
	address : int
		The address of the wallet to link to IMX.
	eth_priv : int
		The private key of the wallet to link to IMX.

	Returns
	----------
	bool : True if the wallet is linked, False if it is not.
	'''
	if is_linked(address):
		return True
	
	print(f"This wallet is not yet linked to IMX, would you like to link it now? (y/n)")
	choice = input()
	if not choice == 'y':
		print("Only wallets linked to Immutable X can trade on the platform, press ENTER to exit...")
		input()
		return False
	link_result = imx_register_address(eth_priv)
	if not "tx_hash" in link_result:
		print(f"Linking wallet failed with message: {link_result}")
		print("Press ENTER to exit...")
		input()
		return False
		
	print(f"Immutable X key for wallet '{hex(address)}' was setup successfully.'")
	return True

def fetch_cards():
	''' Fetches all Gods Unchained cards currently on offer on the Immutable X marketplace

	Returns
	----------
	list : Meteorite versions of all cards that can be bought and sold on the market.
	'''
	meta_data = quote('{"quality":["Meteorite"]}')
	url = f"https://marketplace-api.immutable.com/v1/stacked-assets/0xacb3c6a43d15b907e8433077b6d38ae40936fe2c/search?direction=asc&order_by=buy_quantity_with_fees&page_size=10000&metadata={meta_data}&token_type=ETH"
	data = json.loads(call_retry(request, "GET", url).content)
	cards = [x for x in data["result"]]
	return cards

def search_cards(query : str, cards):
	''' Filter a list of cards for cards whose name contains the query (not case sensitive).

	Parameters
	----------
	query : str
		Text the card name should include in order to be included in the final list.
	cards : list
		A list containing all cards to search for matches.

	Returns
	----------
	list : A list of all cards on the card list where the query is contained in the cards name.
	'''
	query = query.lower()
	results = [card for card in cards if query in card["name"].lower()]
	return results

def card_text(card, eth_price=0):
	''' Format the text on a card into a human readable string.
	
	Parameters
	----------
	card : json
		Card data to create a human readable string for.
	eth_price : float
		The current price of ethereum, this is used to calculate the price of this card on the market.

	Returns
	----------
	str : A human readable string containing information about this card.
	'''
	stats = ""
	price = ""
	if eth_price != 0:
		price = f"(${round(int(card['assets_floor_price']['quantity_with_fees']) / 10**18 * eth_price, 2)})"
	if "attack" in card['asset_stack_search_properties']:
		stats = f"{card['asset_stack_search_properties']['attack']}/{card['asset_stack_search_properties']['health']}"
	card_data = f"{card['name']} {price}\n{card['asset_stack_search_properties']['mana']} mana {stats}\n{card['asset_stack_search_properties'].get('effect', '')}"
	return card_data

def get_balances(address : str):
	''' Get the balances for all tokens on the provided wallet address.

	Parameters
	----------
	address : str
		The wallet address to get the tokens for.

	Returns
	----------
	list : A list of tokens and the associated balance on the provided wallet address.
	'''
	balances = json.loads(call_retry(request, "GET", f"https://api.x.immutable.com/v2/balances/{address}").content)
	balance_data = dict()
	for token in balances["result"]:
		balance_data[token["symbol"]] = int(token["balance"]) / 10**18
	return balance_data

token_list = []
def get_token_list():
	''' Get a list of tokens that can be used to trade on IMX.

	Returns
	----------
	list : The requested list of tokens including their address.
	'''
	global token_list
	if len(token_list) == 0:
		tokens = json.loads(call_retry(request, "GET", "https://api.x.immutable.com/v1/tokens").content)
		token_list = [["ETH", "ETH"]]
		for token in tokens["result"]:
			if "ETH" in token['symbol']:
				continue
			token_list.append([token['symbol'], token["token_address"]])
	return token_list

def request_token():
	''' Asks the user to select a token that can be traded on IMX.

	Returns
	----------
	list : The token that the used selected including the address of the token.
	'''
	tokens = get_token_list()
	for index in range(len(tokens)):
		print(f"{index + 1}. {tokens[index][0]}")
	choice = input()
	return tokens[int(choice) - 1]

def buy_card(card, eth_priv : int):
	''' Prompt the user to buy a meteorite copy of the given card.

	Parameters
	----------
	card : json
		The card that you are looking to buy.
	eth_priv : int
		The private key for the wallet that should be used to buy the card.
	'''
	proto = card['asset_stack_properties']['proto']
	card_data = f'{{"proto":["{proto}"],"quality":["Meteorite"]}}'

	print("What currency would you like to buy with:")
	token = request_token()
	token_str = token[1]
	if token_str == "ETH":
		token_str = "&buy_token_type=ETH"
	url = f"https://api.x.immutable.com/v1/orders?buy_token_address={token_str}&direction=asc&include_fees=true&order_by=buy_quantity&page_size=200&sell_metadata={card_data}&sell_token_address=0xacb3c6a43d15b907e8433077b6d38ae40936fe2c&status=active"
	cards_on_sale = json.loads(call_retry(request, "GET", url).content)["result"]
	
	fees = []

	offers = []
	for offer in cards_on_sale:
		order_id = offer['order_id']
		nft_address = offer['sell']['data']['token_address']
		nft_id = offer['sell']['data']['token_id']
		quantity = int(offer['buy']['data']['quantity'])
		quantity_base = quantity
		for fee in offer['fees']:
			quantity_base -= int(fee['amount'])
		quantity += quantity_base * 0.01
		for fee in fees:
			quantity += quantity_base * (fee.percentage / 100)
		price = quantity / 10**18
		offers.append([order_id, nft_address, nft_id, price])
	offers.sort(key=lambda x: x[3])
	best_offer = offers[0]
	print(f"Buy '{card['name']}' for {best_offer[3]} {token[0]}? (y/n)")
	choice = input()
	print(best_offer)
	if choice == "y":
		print(f"Order finished with the following server response: {imx_buy_nft(best_offer[0], best_offer[1], best_offer[2], token[1], best_offer[3], fees, eth_priv)}")
	else:
		print("Cancelled order, returning to main menu...")

def sell_card(card_data, eth_priv : int):
	''' Prompt the user to sell a meteorite copy of the given card.

	Parameters
	----------
	card_data : json
		The card that you are looking to sell.
	eth_priv : int
		The private key for the wallet that owns the card.
	'''
	nft_address = card_data["token_address"]
	nft_id = card_data["token_id"]
	trade_fee = imx_get_token_trade_fee(nft_address, nft_id) # Get the base trade fee percentage that will be added to the user sale price.

	try: # Request the user to select the currency to sell the card for.
		print("Select the currency to sell for: ")
		token = request_token()
	except (ValueError, IndexError):
		print("Invalid selection, returning to main menu...")
		return

	print("Type the price to sell the card for (including fees):") # Request the user to provide the price they want their card to be listed at.
	try:
		price = float(input())
	except ValueError:
		print("Invalid price, returning to main menu...")
		return

	receive_amount = round(price / (101 + trade_fee) * 100 - 0.5 * 10**-8, 8)
	receive_with_fee = round(price / (200 + trade_fee) * 199 - 0.5 * 10**-8, 8)
	use_fee = False
	print("You can reduce the fee paid by the buyer by receiving part of the sale price as a fee.")
	print(f"Doing so will not change the price for the buyer but will reduce the 'true' fee on this sale from {round(100 * price / receive_amount - 100, 2)}% to {round(100 * price / receive_with_fee - 100, 2)}%")
	print(f"Choosing yes on this option will increase the amount ot {token[0]} paid out to you on a successful sale from {receive_amount} {token[0]} to {receive_with_fee} {token[0]}.")
	print("The downside of using this is that fees are not always paid out immediately after the order settles, usually the fee will be paid out within seconds, but in extraordinary cases it could take up to a few hours after the sale for the funds to arrive.")
	print("Would you like to use this? (y/n)")
	choice = input()
	if choice == "y":
		print(f"The 'true' fee on this order will reduced to {round(100 * price / receive_with_fee - 100, 2)}% (Excludes fees paid out to you.)")
		use_fee = True
	else:
		print(f"The fee on this order will be the standard {round(100 * price / receive_amount - 100, 2)}%")

	fees = []
	if use_fee:
		fees = [FEE(str(hex(eth_get_address(eth_priv))).encode(), 99)]
		receive_amount = receive_with_fee
	
	fee_mult = (101 + trade_fee + sum([x.percentage for x in fees])) / 100
	price = price / fee_mult

	print(f"'{card_data['name']}' will be listed on the market for {round(price * fee_mult, 10)} {token[0]}. If sold, you will recieve {receive_amount} {token[0]}. Would you like to submit this listing? (y/n)")
	choice = input()
	
	if choice == "y":
		print(f"Order finished with the following server response: {imx_sell_nft(nft_address, nft_id, token[1], price, fees, eth_priv)}")
	else:
		print("Cancelled order, returning to main menu...")

def transfer_card(card_data, eth_priv : int):
	''' Prompt the user to sell a meteorite copy of the given card.

	Parameters
	----------
	card_data : json
		The card that you are looking to transfer.
	eth_priv : int
		The private key for the wallet that owns the card.
	'''
	nft_address = card_data["token_address"]
	nft_id = card_data["token_id"]
	print("Type the address to transfer the card to:")
	try:
		transfer_address = int(input(), 16)
	except ValueError:
		print("Invalid address entered, returning to main menu...")
		return
	print(f"Transfer '{card_data['name']}' to '{hex(transfer_address)}'? (y/n).")
	choice = input()
	if choice == "y":
		print(f"Transfer finished with the following server response: {imx_transfer_nft(nft_address, nft_id, transfer_address, eth_priv)}")
	else:
		print("Cancelled transfer, returning to main menu...")

def cancel_orders(order_ids, eth_priv : int):
	''' Cancel orders with the given order IDS.

	Parameters
	----------
	order_ids : list
		The ids for orders you are trying to cancel.
	eth_priv : int
		The private key for the wallet that filed the orders.
	'''
	for order_id in order_ids:
		print(f"Cancel request finished with the following server response: {imx_cancel_order(order_id, eth_priv)}")

def user_select_card(cards, eth_price=0):
	''' Prompt the user to search for and select a card on the market.

	Parameters
	----------
	cards : list
		List of cards to select from.
	eth_price : int
		The current price of ethereum in USD.

	Returns
	----------
	json : The card that was selected.
	'''
	print("Type part of the name to search a card:")
	query = input()
	selection = search_cards(query, cards)
	for index in range(len(selection)):
		print(f"{index + 1}. ", end="")
		endl = "\n   "
		if index > 8:
			endl += " "
		print(card_text(selection[index], eth_price).replace('\n', endl), end="\n\n")
	print("Type the number of the card to select (will return on invalid selection):")
	choice = int(input()) - 1
	return selection[choice]

def trade_card(card, eth_price, address, eth_priv):
	''' Show the menu for trading a selected card.

	Parameters
	----------
	card : json
		The card that was selected for trading.
	eth_price : int
		The current price of ethereum in USD.
	address : int
		The public address of the wallet used for trading.
	eth_priv : int
		The private key of the wallet used for trading.
	'''
	global token_list
	print("-------")
	print(card_text(card, eth_price))
	proto = card['asset_stack_properties']['proto']
	card_data = quote('{"proto":["' + str(proto) + '"],"quality":["Meteorite"]}')
	url = f"https://api.x.immutable.com/v1/assets?page_size=10&user={hex(address)}&metadata={card_data}&sell_orders=true"
	card_data = json.loads(call_retry(request, "GET", url).text)
	num_owned = len(card_data["result"])
	copy = "copy" if num_owned == 1 else "copies"
	print(f"You own {num_owned} meteorite {copy} of this card.")
	order_ids = []
	for owned_card in card_data["result"]:
		if 'orders' in owned_card and 'sell_orders' in owned_card['orders']:
			sale = owned_card['orders']['sell_orders'][0]
			order_ids.append(sale['order_id'])
			token_address = sale.get('contract_address', "ETH")
			try:
				token = next(x for x in get_token_list() if x[1] == token_address)
			except StopIteration:
				token = ["???", "???"]
			price = int(sale['buy_quantity']) / 10**int(sale['buy_decimals'])
			print(f"You have this card on sale for {price} {token[0]} (excluding taker market fee)")
	print("-------")
	print("1. Buy card.")
	if num_owned > 0:
		print("2. Sell card.\n3. Transfer card.")
		if len(order_ids) > 0:
			print("4. Cancel orders.")
	try:
		choice = int(input())
	except ValueError:
		return
	if choice == 1:
		buy_card(card, eth_priv)
	elif choice == 2:
		sell_card(card_data["result"][0], eth_priv)
	elif choice == 3:
		transfer_card(card_data["result"][0], eth_priv)
	elif choice == 4:
		cancel_orders(order_ids, eth_priv)

def transfer_currency(eth_priv):
	''' Show the menu for transfering currency to another wallet.

	Parameters
	----------
	eth_priv : int
		The private key of the wallet used for trading.
	'''
	print("What currency would you like to buy with:")
	token = request_token()
	print(f"Type the amount of {token[0]} to transfer:")
	try:
		amount = float(input())
	except ValueError:
		print("Invalid amount, returning to main menu...")
		return
	print("Type the address to transfer to:")
	try:
		transfer_address = int(input(), 16)
	except ValueError:
		print("Invalid address entered, returning to main menu...")
		return
	print(f"Transfer '{amount}' {token[0]} to '{hex(transfer_address)}'? (y/n).")
	choice = input()
	if choice == "y":
		print(f"Transfer finished with the following server response: {imx_tranfer_token(token[1], amount, transfer_address, eth_priv)}")
	else:
		print("Cancelled transfer, returning to main menu...")

def main():
	''' Show the main menu for trading Gods Unchained cards on Immutable X.
	'''
	eth_priv = prompt_load_wallet()
	address = eth_get_address(eth_priv)
	if not link_wallet(address, eth_priv):
		return
	print(f"Loaded wallet: '{hex(address)}'")
	eth_price = call_retry(get_eth_price)
	cards = call_retry(fetch_cards)
	
	while True:
		balances = call_retry(get_balances, str(hex(address)))
		print("--- Account Balances ---")
		for currency in balances:
			print(f"{balances[currency]} {currency}")
		print("--- Main Menu ---")
		print("1. Select card to trade\n2. Transfer currency\n3. Export private key\n4. Exit")
		choice = input()
		print(choice)
		if (choice == "1"):
			try:
				card_to_trade = user_select_card(cards, eth_price)
			except (ValueError, IndexError):
				print("No card selected, returning to main menu.")
				continue
			trade_card(card_to_trade, eth_price, address, eth_priv)
		elif (choice == "2"):
			transfer_currency(eth_priv)
		elif (choice == "3"):
			print("This will display the current wallets private key, continue? (y/n)")
			choice = input()
			if (choice == "y"):
				print(f"PRIVATE KEY: {hex(eth_priv)}")
		elif (choice == "4"):
			break



if __name__ == "__main__":
	main() # Entry point for the program. Load the main function.