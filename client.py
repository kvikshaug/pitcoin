import time
import os

from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages

# Configure Django settings before importing local code
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db.settings")

from address import AddressBook
from sync import Synchronizer

# class BTCClient(BitcoinClient):
#     def __init__(self, *args, **kwargs):
#         super(BTCClient, self).__init__(*args, **kwargs)
#         self.address_book = []

#     def on_handshake(self):
#         self.send_message(messages.GetAddr())

#     def handle_block(self, message_header, message):
#         print("Handling block")
#         print(message)
#         print("Block hash: %s" % message.calculate_hash())

#     def handle_inv(self, message_header, message):
#         print("Handling inv")
#         getdata = messages.GetData()
#         getdata.inventory = message.inventory
#         self.send_message(getdata)

#     def handle_message_header(self, message_header, payload):
#         print("<- %s" % message_header)

#     def handle_send_message(self, message_header, message):
#         print("-> %s" % message_header)

print("1. Fetching addresses...")
AddressBook.bootstrap()
AddressBook.keep_updated()
print("   Got %s initial addresses." % len(AddressBook.addresses))

print("2. Synchronizing all blocks...")
Synchronizer.synchronize()

print("3. Done!")



# while True:
#     client = BTCClient(random.choice(seed_addresses), coin='bitcoin_testnet3')
#     client.handshake()
#     client.loop()
