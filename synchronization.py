from datetime import datetime
import random

from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages

from models import Address

class BTCClient(BitcoinClient):
    def __init__(self, *args, **kwargs):
        super(BTCClient, self).__init__(*args, **kwargs)

    def on_handshake(self):
        self.send_message(messages.GetBlocks())

    def handle_block(self, message_header, message):
        print("Handling block")
        print(message)
        print("Block hash: %s" % message.calculate_hash())

    def handle_inv(self, message_header, message):
        print("Handling inv")
        getdata = messages.GetData()
        getdata.inventory = message.inventory
        self.send_message(getdata)

    def handle_message_header(self, message_header, payload):
        print("<- %s" % message_header)

    def handle_send_message(self, message_header, message):
        print("-> %s" % message_header)
