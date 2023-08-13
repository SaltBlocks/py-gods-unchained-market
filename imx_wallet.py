from IMXlib import *
import http.server
import socketserver
from requests import request
import json
import threading
import queue

class imx_wallet:
    def __init__(self, eth_key):
        self.eth_key = eth_key
        self.address = eth_get_address(self.eth_key)
    
    def get_address(self):
        return self.address

    def is_linked(self):
        url = f"https://api.x.immutable.com/v1/users/{hex(self.address)}"
        link_data = request("GET", url).text
        return not "Account not found" in link_data
    
    def get_balances(self):
        ''' Get the balances for all tokens in the provided wallet address.
        
        Parameters
        ----------
        address : str
            The wallet address to get the tokens for.

        Returns
        ----------
        list : A list of tokens and the associated balance on the provided wallet address.
        '''
        balances = json.loads(request("GET", f"https://api.x.immutable.com/v2/balances/{hex(self.address)}").content)
        balance_data = dict()
        for token in balances["result"]:
            balance_data[token["symbol"]] = int(token["balance"]) / 10**18
        return balance_data

    def register_address(self):
        return imx_register_address(self.eth_key)
    
    def sell_nft(self, nft_address, nft_id, token_id, price: float, fees):
        return imx_sell_nft(nft_address, nft_id, token_id, price, fees, self.eth_key)
    
    def cancel_order(self, order_id):
        return imx_cancel_order(order_id, self.eth_key)
        
    def transfer_nft(self, nft_address, nft_id, receiver_address):
        return imx_transfer_nft(nft_address, nft_id, receiver_address, self.eth_key)
    
    def transfer_token(self, token_id, amount: float, receiver_address):
        return imx_transfer_token(token_id, amount, receiver_address, self.eth_key)
    
    def buy_nft(self, order_id, price : float, fees):
        return imx_buy_nft(order_id, price, fees, self.eth_key)

class imx_web_wallet(imx_wallet):
    def __init__(self):
        global PORT
        imx_seed_msg = imx_get_seed_msg()
        request_signature(imx_seed_msg, "Connect the signing wallet to pyGUMarket.")
        print(f"Please go to 'http://localhost:{PORT}/' to connect your web wallet to pyGUMarket...")
        result = signature_queue.get()
        finish_signature_request()
        if result["message"] == imx_seed_msg:
            self.address = int(result["address"], 16)
            self.imx_seed = int(result["signature"], 16)
            print(f"Wallet '{hex(self.address)}' successfully connected to pyGUMarket.")
        else:
            raise AssertionError(f"Signed message {result['message']} does not match the IMX seed message needed for signing transactions.")
    
    def register_address(self):
        global PORT
        imx_link_msg = imx_get_link_msg()
        request_signature(imx_link_msg, "Link your wallet to IMX.")
        print(f"Please go to 'http://localhost:{PORT}/' to link your web wallet to IMX...")
        result = signature_queue.get()
        finish_signature_request()
        if result["message"] == imx_link_msg and result["address"] == str(hex(self.address)):
            return imx_register_address_presign(self.address, self.imx_seed, result["signature"])
        else:
            raise AssertionError(f"Signed message {result['message']} or address {result['address']} does not match the requested data.")
    
    def sell_nft(self, nft_address, nft_id, token_id, price: float, fees):
        data = json.loads(imx_request_sell_nft(nft_address, nft_id, token_id, price, fees, self.address))
        nonce = data["nonce"]
        request_signature(data["signable_message"], f"Create a sell order for an NFT with ID {nft_id} and address {nft_address}.")
        print(f"Please go to 'http://localhost:{PORT}/' to sign the sell order...")
        result = signature_queue.get()
        finish_signature_request()
        if result["message"] == data["signable_message"] and result["address"] == str(hex(self.address)):
            return imx_finish_sell_or_offer_nft(nonce, self.imx_seed, result["signature"])
        else:
            raise AssertionError(f"Signed message {result['message']} or address {result['address']} does not match the requested data.")
    
    def cancel_order(self, order_id):
        signable_message = imx_request_cancel_order(order_id)
        request_signature(signable_message, f"Cancel an active order with ID {order_id}.")
        print(f"Please go to 'http://localhost:{PORT}/' to sign the cancel order...")
        result = signature_queue.get()
        finish_signature_request()
        if result["message"] == signable_message and result["address"] == str(hex(self.address)):
            return imx_finish_cancel_order(order_id, self.address, self.imx_seed, result["signature"])
        else:
            raise AssertionError(f"Signed message {result['message']} or address {result['address']} does not match the requested data.")
        
    def transfer_nft(self, nft_address, nft_id, receiver_address):
        data = json.loads(imx_request_transfer_nft(nft_address, nft_id, receiver_address, self.address))
        nonce = data["nonce"]
        request_signature(data["signable_message"], f"Transfer an NFT with ID {nft_id} and address '{nft_address}' to '{hex(receiver_address)}'.")
        print(f"Please go to 'http://localhost:{PORT}/' to sign the transfer order...")
        result = signature_queue.get()
        finish_signature_request()
        if result["message"] == data["signable_message"] and result["address"] == str(hex(self.address)):
            return imx_finish_transfer(nonce, self.imx_seed, result["signature"])
        else:
            raise AssertionError(f"Signed message {result['message']} or address {result['address']} does not match the requested data.")
    
    def transfer_token(self, token_id, amount: float, receiver_address):
        data = json.loads(imx_request_transfer_token(token_id, amount, receiver_address, self.address))
        nonce = data["nonce"]
        request_signature(data["signable_message"], f"Transfer {amount} of token with ID '{token_id}' to '{hex(receiver_address)}'.")
        print(f"Please go to 'http://localhost:{PORT}/' to sign the transfer order...")
        result = signature_queue.get()
        finish_signature_request()
        if result["message"] == data["signable_message"] and result["address"] == str(hex(self.address)):
            return imx_finish_transfer(nonce, self.imx_seed, result["signature"])
        else:
            raise AssertionError(f"Signed message {result['message']} or address {result['address']} does not match the requested data.")
    
    def buy_nft(self, order_id, price : float, fees):
        data = json.loads(imx_request_buy_nft(order_id, self.address, fees))
        nonce = data["nonce"]
        request_signature(data["signable_message"], f"Buy order with ID {order_id} for up to '{price}' of the sale token.")
        print(f"Please go to 'http://localhost:{PORT}/' to sign the buy order...")
        result = signature_queue.get()
        finish_signature_request()
        if result["message"] == data["signable_message"] and result["address"] == str(hex(self.address)):
            return imx_finish_buy_nft(nonce, price, self.imx_seed, result["signature"])
        else:
            raise AssertionError(f"Signed message {result['message']} or address {result['address']} does not match the requested data.")

signature_queue = queue.Queue()
message_to_sign = ""
action_to_perform = ""

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>pyGUMarket message signing page</title>
</head>
<body>
    <h1>Sign messages for pyGUMarket using Web Wallet</h1>
    <p>Signing the message will perform the following action:</p>
    <p id="actionText"></p>
    <script>
        async function fetchMessage() {
            const response = await fetch('http://localhost:8080/message');
            const message = await response.text();
            return message;
        }
        async function displayActiveAction() {
            const response = await fetch('http://localhost:8080/action');
            const action = await response.text();
            if (!action.includes("Connect"))
                document.getElementById("switchButton").style.visibility = 'hidden';
            const actionTextElement = document.getElementById("actionText");
            actionTextElement.textContent = action;
        }
        async function signMessage(message) { 
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            const signature = await window.ethereum.request({ method: 'personal_sign', params: [message, accounts[0]] });
            const data = JSON.stringify({ address: accounts[0], message: message, signature: signature });
            const response = await fetch('http://localhost:8080/signature', { method: 'POST', body: data });
            const actionTextElement = document.getElementById("actionText");
            actionTextElement.textContent = "Message signed and sent to pyGUMarket, refresh the page or click 'Sign message' again to check for new messages.";
            document.getElementById("switchButton").style.visibility = 'hidden';
        }
        async function fetchAndSignMessage()
        {
            displayActiveAction()    
            const message = await fetchMessage();
            if (message.length == 0)
                alert("No message to sign")
            else
                signMessage(message);
        }
        async function switchWallet() {
            try {
                await window.ethereum.request({ method: 'wallet_requestPermissions', params: [{ eth_accounts: {} }] });
                alert("Wallet switched successfully");
            } catch (error) {
                console.error("Error switching wallet:", error);
                alert("Error switching wallet. Check console for details.");
            }
        }
        window.onload = function() { 
                displayActiveAction();
            }
    </script>
    <button onclick = "fetchAndSignMessage()">Sign message</button> 
    <button id="switchButton" onclick = "switchWallet()"> Switch wallet </button> 
</body>
</html>
"""

class CustomRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logging of requests
    
    def do_GET(self):
        self.send_response(200)
        if (self.path == "/message"):
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(message_to_sign.encode())
        elif (self.path == "/action"):
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            action_text = action_to_perform
            if (len(message_to_sign) == 0):
                action_text = "No message available for signing, refresh the page or click 'Sign message' to check for new messages."
            elif (len(action_text) == 0):
                action_text = f"Sign the message '{message_to_sign}' to complete an action in pyGUMarket."
            self.wfile.write(action_text.encode())
        else:
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())

    def do_POST(self):
        if (self.path == "/signature"):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            signature_queue.put(data)
            self.send_response(200)
            self.end_headers()

def run_server():
    global http_server
    global PORT
    # Set up the server
    PORT = 8080
    Handler = CustomRequestHandler

    # Start the server
    with socketserver.TCPServer(("", PORT), Handler) as http_server:
        #print(f"Server started at http://localhost:{PORT}")
        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            pass

def shutdown_server():
    global http_server
    if 'http_server' in globals():
        http_server.shutdown()

def request_signature(message, action=""):
    global http_server
    global message_to_sign
    global action_to_perform
    if not 'http_server' in globals():
        server = threading.Thread(target=run_server, args=());
        server.start()
    message_to_sign = message
    action_to_perform = action

def finish_signature_request():
    global message_to_sign
    message_to_sign = ""
    action_to_perform = ""

def main():
    wallet = imx_web_wallet()
    #print(wallet.cancel_order(317933507))
    print(wallet.transfer_token("ETH", 0.000001, "0xA11738D1eD318FB27b2D37ab96AdF0eAb72b5ff4"))
    #print(wallet.sell_nft("0xacb3c6a43d15b907e8433077b6d38ae40936fe2c", "182567518", "ETH", 5, []))
    input()
    http_server.shutdown()

if __name__ == "__main__":
    main()