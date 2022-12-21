from Crypto.Protocol.KDF import PBKDF2
from Crypto import Random
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
import pickle
from getpass import getpass
from IMXlib import eth_get_address, eth_generate_key
import os


def get_encryption_key(password, salt):
	''' Calculate an AES256 encryption key for the given password and hash.

	Parameters
	----------
	password : str
		The password used to secure the key.
	salt : bytes
		bytes to use as a salt when generating the key.
	Returns
	----------
	bytes : The encryption key as a byte string.
	'''
	return PBKDF2(password.encode("utf-8"), salt, 32, 10**6)

def encrypt(data, key):
	''' Encrypt the provided data with the given AES256 key.

	Parameters
	----------
	data : bytes
		The data to encrypt as a byte string.
	key : bytes
		Encryption key to encrypt the data with.
	Returns
	----------
	str : base64 encoded string containing the encrypted data.
	'''
	pad_len = AES.block_size - len(data) % AES.block_size
	pad_data = bytes([pad_len]) * pad_len
	raw_data = data + pad_data
	nonce = Random.new().read(AES.block_size)
	cipher = AES.new(key, AES.MODE_CBC, nonce)
	data = nonce + cipher.encrypt(raw_data)
	return b64encode(data)

def decrypt(data, key):
	''' Decrypt the provided data with the given AES256 key.

	Parameters
	----------
	data : str
		The data to decrypt as a base64 encoded string.
	key : bytes
		Encryption key to decrypt the data with.
	Returns
	----------
	bytes : The decrypted data as a byte string.
	'''
	data_enc = b64decode(data)
	nonce = data_enc[:AES.block_size]
	cipher = AES.new(key, AES.MODE_CBC, nonce)
	data = cipher.decrypt(data_enc[AES.block_size:])
	pad_len = data[-1]
	if data[-pad_len:] != bytes([pad_len]) * pad_len:
		raise ValueError("Incorrect Key.")
	decrypted = data[:-pad_len]
	return decrypted

def save_wallet(eth_key : int, password : str):
	''' Store the given ethereum private key in a file secured with the provided password.

	Parameters
	----------
	eth_key : int
		The private key to store.
	password : str
		The password to secure the key with.
	'''
	address = eth_get_address(eth_key)
	salt = Random.new().read(32)
	enc_data = encrypt(eth_key.to_bytes(32, "big"), get_encryption_key(password, salt))
	with open(f"wallet_{hex(address)}.wlt", "wb") as wallet_file:
		pickle.dump(address, wallet_file)
		pickle.dump(salt, wallet_file)
		pickle.dump(enc_data, wallet_file)

def load_wallet_address(file_name : str):
	''' Read the public address from a password protected private key file.

	Parameters
	----------
	file_name : str
		Path to the file the wallet is stored in.
	Returns
	----------
	int : The public address associated with the wallet.
	'''
	with open(file_name, "rb") as wallet_file:
		address = pickle.load(wallet_file)
	return address

def load_wallet(file_name : str, password : str):
	''' Attempt to recover the private key from a stored wallet using the provided password.

	Parameters
	----------
	file_name : str
		Path to the file the wallet is stored in.
	Returns
	----------
	int : The private key associated with the wallet.
	'''
	with open(file_name, "rb") as wallet_file:
		pickle.load(wallet_file)
		salt = pickle.load(wallet_file)
		enc_data = pickle.load(wallet_file)
	enc_key = get_encryption_key(password, salt)
	return int.from_bytes(decrypt(enc_data, enc_key), "big")

def prompt_load_wallet():
	''' Prompt the user to load or create a wallet.

	Returns
	----------
	int : The private key associated with the loaded wallet.
	'''
	wallets = []
	for file_name in os.listdir():
		if os.path.isfile(file_name) and file_name.endswith(".wlt"):
			wallets.append(file_name)
	for i in range(len(wallets)):
		name = wallets[i][:-4]
		address = str(hex(load_wallet_address(wallets[i])))
		print(f"{i + 1}. {name} ({address[0:6]}...{address[-4:]})")
	print(f"{len(wallets) + 1}. Add new wallet.")

	while True:
		try:
			choice = int(input())
			if choice > 0 and choice <= len(wallets) + 1:
				break
		except ValueError:
			pass
	
	if choice == len(wallets) + 1:
		eth_priv = getpass("Enter ETH private key, leave blank for a random key (typed characters are hidden): ")
		if len(eth_priv) == 0:
			eth_priv = eth_generate_key()
		if not isinstance(eth_priv, int):
			eth_priv = int(eth_priv, 16)
		print(f"Storing key for address: {hex(eth_get_address(eth_priv))}")
		
		while True:
			password = getpass("Enter a password to secure the wallet with: ")
			security_check = getpass("Please Re-enter the same password: ")
			if (password == security_check):
				break
			print("Passwords don't match, press ENTER to try again.")
			input()
		save_wallet(eth_priv, password)
		print(f"Created and loaded wallet for address: {hex(eth_get_address(eth_priv))}")
	else:
		while True:
			try: 
				password = getpass(f"Enter the password for the wallet '{hex(load_wallet_address(wallets[choice - 1]))}': ")
				eth_priv = load_wallet(wallets[choice - 1], password)
				break
			except ValueError:
				print("Incorrect password, try again.")
	
	return eth_priv

def main():
	print(hex(prompt_load_wallet()))

if __name__ == "__main__":
	main()