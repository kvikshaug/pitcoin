import time

from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages

from address import AddressBook


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
address_book = AddressBook()
address_book.bootstrap()
address_book.start()
print("   Got %s initial addresses." % len(address_book.addresses))

print("2. Synchronizing all blocks...")
address = address_book.get_address()



# while True:
#     client = BTCClient(random.choice(seed_addresses), coin='bitcoin_testnet3')
#     client.handshake()
#     client.loop()
