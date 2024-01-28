''' Python Command line utility for trading Gods Unchained cards on the Immutable X platform.

This is intended as a testing/example program for the IMXlib library.
Keys are securely stored using AES256 encryption. The key storing mechanism is implemented in key_loader.py.

Functions for interacting with Immutable X are implemented in IMXlib.py and used by imx_wallet.py.
'''

from key_loader import prompt_load_wallet
from IMXlib import imx_get_token_trade_fee, FEE, vcredist_installed
from requests import request
from urllib.parse import quote
from imx_wallet import imx_wallet, imx_web_wallet, shutdown_server
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

def link_wallet(wallet):
    ''' Make sure the wallet is linked to IMX, if it isn't, ask to set it up for the user.
        Unless you've never connected this wallet to IMX before, this should already be done.

    Parameters
    ----------
    wallet : imx_wallet
        The wallet to link to IMX.

    Returns
    ----------
    bool : True if the wallet is linked, False if it is not.
    '''
    if wallet.is_linked():
        return True
    
    print(f"This wallet is not yet linked to IMX, would you like to link it now? (y/n)")
    choice = input()
    if not choice == 'y':
        print("Only wallets linked to Immutable X can trade on the platform, press ENTER to exit...")
        input()
        return False
    link_result = wallet.register_address()
    if not "tx_hash" in link_result:
        print(f"Linking wallet failed with message: {link_result}")
        print("Press ENTER to exit...")
        input()
        return False
        
    print(f"Immutable X key for wallet '{hex(wallet.address)}' was setup successfully.'")
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
    list : The token that the user selected including the address of the token.
    '''
    tokens = get_token_list()
    for index in range(len(tokens)):
        print(f"{index + 1}. {tokens[index][0]}")
    choice = input()
    return tokens[int(choice) - 1]

def buy_card(card, wallet: imx_wallet):
    ''' Prompt the user to buy a meteorite copy of the given card.

    Parameters
    ----------
    card : json
        The card that you are looking to buy.
    wallet : imx_wallet
        The wallet that should be used to buy the card.
    '''
    proto = card['asset_stack_properties']['proto']
    card_data = f'{{"proto":["{proto}"],"quality":["Meteorite"]}}'

    print("What currency would you like to buy with:")
    token = request_token()
    token_str = token[1]
    if token_str == "ETH":
        token_str = "&buy_token_type=ETH"
    url = f"https://api.x.immutable.com/v3/orders?buy_token_address={token_str}&direction=asc&include_fees=true&order_by=buy_quantity&page_size=200&sell_metadata={card_data}&sell_token_address=0xacb3c6a43d15b907e8433077b6d38ae40936fe2c&status=active"
    cards_on_sale = json.loads(call_retry(request, "GET", url).content)["result"]
    fees = []
    #fees = [FEE(str(hex(wallet.get_address())).encode(), 0.1)] #example of an added 0.1% fee. Transferred to the sellers wallet.

    fee_added_multiplier = 0.01
    for fee in fees:
        fee_added_multiplier += fee.percentage / 100
    offers = []
    for offer in cards_on_sale:
        order_id = offer['order_id']
        token_id = offer['sell']['data']['token_id']
        token_address = offer['sell']['data']['token_address']
        quantity = int(offer['buy']['data']['quantity'])
        decimals = int(offer['buy']['data']['decimals'])
        quantity_with_fees = int(offer['buy']['data']['quantity_with_fees'])
        quantity_total = (quantity_with_fees + quantity * fee_added_multiplier) / 10**decimals
        offers.append([order_id, quantity_total, token_id, token_address])
    offers.sort(key=lambda x: x[1])
    best_offer = offers[0]
    print(f"'{card['name']}' is available for {best_offer[1]:.10f} {token[0]}.")
    print(f"1. Buy now.")
    print(f"2. Create buy offer.")
    print(f"3. Cancel.")
    choice = input()
    if choice == "1":
        print(f"Buy '{card['name']}' for {best_offer[1]:.10f} {token[0]}? (y/n)")
        choice = input()
        if choice == "y":
            print(f"Order finished with the following server response: {wallet.buy_order(best_offer[0], best_offer[1], fees)}")
        else:
            print("Cancelled order, returning to main menu...")
    elif choice == "2":
        offer_card(best_offer, token, wallet)
    else:
        print("Cancelled order, returning to main menu...")    

def buy_cosmetic(wallet : imx_wallet):
    ''' Prompt the user to buy a cosmetic item for GU.

    Parameters
    ----------
    wallet : imx_wallet
        The wallet that should be used to buy the cosmetic.
    '''
    print("No search function for these just yet :(.")
    print("What is the proto_id of the cosmetic you'd like to buy?")
    proto = input();
    url = f"https://api.x.immutable.com/v3/orders?buy_token_type=ETH&direction=asc&include_fees=true&order_by=buy_quantity&page_size=200&sell_metadata=%257B%2522proto%2522%253A%255B%2522{proto}%2522%255D%257D&sell_token_address=0x7c3214ddc55dfd2cac63c02d0b423c29845c03ba&status=active"
    cosmetics_on_sale = json.loads(call_retry(request, "GET", url).content)["result"]
    cosmetic_name = cosmetics_on_sale[0]["sell"]["data"]["properties"]["name"]
    print(f"Buying: {cosmetic_name}")
    
    fees = []

    offers = []
    for offer in cosmetics_on_sale:
        order_id = offer['order_id']
        quantity = int(offer['buy']['data']['quantity'])
        quantity_with_fees = int(offer['buy']['data']['quantity_with_fees'])
        quantity_total = (quantity_with_fees + quantity * 0.01) / 10**18
        offers.append([order_id, quantity_total])
    offers.sort(key=lambda x: x[1])
    best_offer = offers[0]
    print(f"Buy '{cosmetic_name}' for {best_offer[1]:.10f} ETH? (y/n)")
    choice = input()
    if choice == "y":
        print(f"Order finished with the following server response: {wallet.buy_order(best_offer[0], best_offer[1], fees)}")
    else:
        print("Cancelled order, returning to main menu...")

def sell_card(card_data, wallet : imx_wallet):
    ''' Prompt the user to sell a meteorite copy of the given card.

    Parameters
    ----------
    card_data : json
        The card that you are looking to sell.
    wallet : imx_wallet
        The wallet that owns the card.
    '''
    nft_address = card_data["token_address"]
    nft_id = card_data["token_id"]
    trade_fee = imx_get_token_trade_fee(nft_address, nft_id) + 1 # Get the trade fee percentage that will be added to the user sale price, we'll assume the buyer marketplace charges 1%.

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

    fees = []
    #fees = [FEE(str(hex(wallet.get_address())).encode(), 0.1)] #example of an added 0.1% fee. Transferred to the sellers wallet.
    
    fee_subtracted_multiplier = 0.99
    for fee in fees:
        fee_subtracted_multiplier -= fee.percentage / 100
    price_base = price / (100 + trade_fee) * 100
    amount_receive = price / (100 + trade_fee) * 100 * fee_subtracted_multiplier
    
    print(f"'{card_data['name']}' will be listed on the market for {price:.10f} {token[0]}. If sold, you will recieve {amount_receive:.10f} {token[0]}. Would you like to submit this listing? (y/n)")
    choice = input()
    
    if choice == "y":
        print(f"Order finished with the following server response: {wallet.sell_nft(nft_address, nft_id, token[1], price_base, fees)}")
    else:
        print("Cancelled order, returning to main menu...")

def offer_card(card_data, token, wallet : imx_wallet):
    ''' Prompt the user to create a buy offer for a meteorite copy of the given card.

    Parameters
    ----------
    card_data : json
        The card that you are looking to sell.
    wallet : imx_wallet
        The wallet that owns the card.
    '''
    nft_address = card_data[3]
    nft_id = card_data[2]
    trade_fee = imx_get_token_trade_fee(nft_address, nft_id) + 1 # Get the trade fee percentage that will be added to the user sale price, we'll assume the buyer marketplace charges 1%.

    print("Type the price you are willing to pay (including fees):") # Request the user to provide the price they want their card to be listed at.
    try:
        price = float(input())
    except ValueError:
        print("Invalid price, returning to main menu...")
        return

    fees = []
    #fees = [FEE(str(hex(wallet.get_address())).encode(), 0.1)] #example of an added 0.1% fee. Transferred to the sellers wallet.
    
    fee_added_multiplier = 1.01
    for fee in fees:
        fee_added_multiplier += fee.percentage / 100
    price_base = price / fee_added_multiplier
    amount_receive = price_base - price_base * trade_fee / 100;
    
    print(f"An offer will be created which if accepted, will cost you {price:.10f} {token[0]}. If accepted, the seller will recieve {amount_receive:.10f} {token[0]}. Would you like to submit this listing? (y/n)")
    choice = input()
    
    if choice == "y":
        print(f"Order finished with the following server response: {wallet.offer_nft(nft_address, nft_id, token[1], price_base, fees)}")
    else:
        print("Cancelled order, returning to main menu...")

def transfer_card(card_data, wallet : imx_wallet):
    ''' Prompt the user to sell a meteorite copy of the given card.

    Parameters
    ----------
    card_data : json
        The card that you are looking to transfer.
    wallet : imx_wallet
        The wallet that owns the card.
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
        print(f"Transfer finished with the following server response: {wallet.transfer_nft(nft_address, nft_id, transfer_address)}")
    else:
        print("Cancelled transfer, returning to main menu...")

def cancel_orders(order_ids, wallet : imx_wallet):
    ''' Cancel orders with the given order IDs.

    Parameters
    ----------
    order_ids : list
        The ids for orders you are trying to cancel.
    wallet : imx_wallet
        The wallet that filed the orders.
    '''
    for order_id in order_ids:
        print(f"Cancel request finished with the following server response: {wallet.cancel_order(order_id)}")

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

def trade_card(card, eth_price, wallet : imx_wallet):
    ''' Show the menu for trading a selected card.

    Parameters
    ----------
    card : json
        The card that was selected for trading.
    eth_price : int
        The current price of ethereum in USD.
    wallet : imx_wallet
        The wallet used for trading.
    '''
    global token_list
    print("-------")
    print(card_text(card, eth_price))
    proto = card['asset_stack_properties']['proto']
    card_metadata = quote('{"proto":["' + str(proto) + '"],"quality":["Meteorite"]}')
    url = f"https://api.x.immutable.com/v1/assets?page_size=10&user={hex(wallet.address)}&metadata={card_metadata}&sell_orders=true"
    card_data = json.loads(call_retry(request, "GET", url).text)
    url = f"https://api.x.immutable.com/v3/orders?status=active&buy_metadata={card_metadata}&order_by=sell_quantity&direction=desc&user={hex(wallet.address)}&page_size=200"
    offer_data = json.loads(call_retry(request, "GET", url).text)
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
    for offer in offer_data["result"]:
        order_ids.append(offer["order_id"])
    print(f"You have {len(offer_data['result'])} outstanding buy offer for this card.")
    print("-------")
    print("1. Buy card.")
    if num_owned > 0:
        print("2. Sell card.\n3. Transfer card.")
    if len(order_ids) > 0:
        num = 2
        if num_owned > 0:
            num = 4
        print(f"{num}. Cancel orders.")
    try:
        choice = int(input())
    except ValueError:
        return
    if choice == 1:
        buy_card(card, wallet)
    elif choice == 2:
        if (num_owned > 0):
            sell_card(card_data["result"][0], wallet)
        else:
            cancel_orders(order_ids, wallet)
    elif choice == 3:
        transfer_card(card_data["result"][0], wallet)
    elif choice == 4:
        cancel_orders(order_ids, wallet)

def transfer_currency(wallet : imx_wallet):
    ''' Show the menu for transfering currency to another wallet.

    Parameters
    ----------
    wallet : imx_wallet
        The wallet used for trading.
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
    print(f"Transfer '{amount:.10f}' {token[0]} to '{hex(transfer_address)}'? (y/n).")
    choice = input()
    if choice == "y":
        print(f"Transfer finished with the following server response: {wallet.transfer_token(token[1], amount, transfer_address)}")
    else:
        print("Cancelled transfer, returning to main menu...")

def main():
    ''' Show the main menu for trading Gods Unchained cards on Immutable X.
    '''

    wallet = prompt_load_wallet()
    if not link_wallet(wallet):
        shutdown_server()
        return
    print(f"Loaded wallet: '{hex(wallet.address)}'")
    print("Fetching currency prices...")
    eth_price = call_retry(get_eth_price)
    print("Fetching GU cards...")
    cards = call_retry(fetch_cards)
    
    while True:
        balances = call_retry(wallet.get_balances)
        print("--- Account Balances ---")
        for currency in balances:
            print(f"{balances[currency]} {currency}")
        print("--- Main Menu ---")
        print("1. Select card to trade\n2. Buy GU Cosmetic\n3. Transfer currency\n4. Export private key\n5. Exit")
        choice = input()
        print(choice)
        if (choice == "1"):
            try:
                card_to_trade = user_select_card(cards, eth_price)
            except (ValueError, IndexError):
                print("No card selected, returning to main menu.")
                continue
            trade_card(card_to_trade, eth_price, wallet)
        elif (choice == "2"):
            buy_cosmetic(wallet)
        elif (choice == "3"):
            transfer_currency(wallet)
        elif (choice == "4"):
            if isinstance(wallet, imx_web_wallet):
                print("The private key of this wallet is not accessible to pyGUMarket.")
            else:
                print("This will display the current wallets private key, continue? (y/n)")
                choice = input()
                if (choice == "y"):
                    print(f"PRIVATE KEY: {hex(wallet.eth_key)}")
        elif (choice == "5"):
            break
    shutdown_server()

if __name__ == "__main__":
    main() # Entry point for the program. Load the main function.