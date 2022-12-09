from key_loader import prompt_load_wallet
from IMXlib import eth_get_address, imx_sell_nft, imx_buy_nft, imx_transfer_nft, imx_cancel_order, FEE
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

def fetch_cards():
	meta_data = quote('{"quality":["Meteorite"]}')
	url = f"https://marketplace-api.immutable.com/v1/stacked-assets/0xacb3c6a43d15b907e8433077b6d38ae40936fe2c/search?direction=asc&order_by=buy_quantity_with_fees&page_size=10000&metadata={meta_data}&token_type=ETH"
	data = json.loads(call_retry(request, "GET", url).content)
	cards = [x for x in data["result"]]
	return cards

def search_cards(query : str, cards):
	query = query.lower()
	results = [card for card in cards if query in card["name"].lower()]
	return results

def card_text(card, eth_price=0):
	stats = ""
	price = ""
	if eth_price != 0:
		price = f"(${round(int(card['assets_floor_price']['quantity_with_fees']) / 10**18 * eth_price, 2)})"
	if "attack" in card['asset_stack_search_properties']:
		stats = f"{card['asset_stack_search_properties']['attack']}/{card['asset_stack_search_properties']['health']}"
	card_data = f"{card['name']} {price}\n{card['asset_stack_search_properties']['mana']} mana {stats}\n{card['asset_stack_search_properties'].get('effect', '')}"
	return card_data

def get_balances(address : str):
	balances = json.loads(call_retry(request, "GET", f"https://api.x.immutable.com/v2/balances/{address}").content)
	balance_data = dict()
	for token in balances["result"]:
		balance_data[token["symbol"]] = int(token["balance"]) / 10**18
	return balance_data

token_list = []
def get_token_list():
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
	tokens = get_token_list()
	for index in range(len(tokens)):
		print(f"{index + 1}. {tokens[index][0]}")
	choice = input()
	return tokens[int(choice) - 1]

def buy_card(card, address, eth_priv : int):
	proto = card['asset_stack_properties']['proto']
	card_data = f'{{"proto":["{proto}"],"quality":["Meteorite"]}}'

	print("What currency would you like to buy with:")
	token = request_token()
	print(card_data)
	print(token)
	token_str = token[1]
	if token_str == "ETH":
		token_str = "&buy_token_type=ETH"
	url = f"https://api.x.immutable.com/v1/orders?buy_token_address={token_str}&direction=asc&include_fees=true&order_by=buy_quantity&page_size=200&sell_metadata={card_data}&sell_token_address=0xacb3c6a43d15b907e8433077b6d38ae40936fe2c&status=active"
	cards_on_sale = json.loads(call_retry(request, "GET", url).content)["result"]
	
	fees = []#[FEE(b"0x926268e740a64d9efa377a26553fd522dc70c053", 10)]

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

def sell_card(card_data, address, eth_priv : int):
	nft_address = card_data["token_address"]
	nft_id = card_data["token_id"]

	try:
		print("Select the currency to sell for: ")
		token = request_token()
	except (ValueError, IndexError):
		print("Invalid selection, returning to main menu...")
		return

	print("Type the price to sell the card for (excluding fees):")
	try:
		price = float(input())
	except ValueError:
		print("Invalid price, returning to main menu...")
		return

	print(f"Sell card '{card_data['name']}' for {price} {token[0]}? (y/n)")
	choice = input()
	fees = []#[FEE(str(hex(address)).encode(), 92)]
	if choice == "y":
		print(f"Order finished with the following server response: {imx_sell_nft(nft_address, nft_id, token[1], price, fees, eth_priv)}")
	else:
		print("Cancelled order, returning to main menu...")

def transfer_card(card_data, eth_priv : int):
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
	for order_id in order_ids:
		print(f"Cancel request finished with the following server response: {imx_cancel_order(order_id, eth_priv)}")

def user_select_card(cards, eth_price):
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
			print(f"You have this card on sale for {price} {token[0]}")
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
		buy_card(card, address, eth_priv)
	elif choice == 2:
		sell_card(card_data["result"][0], address, eth_priv)
	elif choice == 3:
		transfer_card(card_data["result"][0], eth_priv)
	elif choice == 4:
		cancel_orders(order_ids, eth_priv)
	

def main():
	eth_priv = prompt_load_wallet()
	address = eth_get_address(eth_priv)
	print(f"Loaded wallet: '{hex(address)}'")
	eth_price = call_retry(get_eth_price)
	cards = call_retry(fetch_cards)
	
	while True:
		balances = call_retry(get_balances, str(hex(address)))
		print("--- Account Balances ---")
		for currency in balances:
			print(f"{balances[currency]} {currency}")
		print("--- Main Menu ---")
		print("1. Select card to trade\n2. Exit")
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
			break



if __name__ == "__main__":
	main()