from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages, structures, values

from db.models import Block

def run():
    client = TestClient("as")
    client.handshake()
    client.loop()

class TestClient(BitcoinClient):
    def __init__(self, *args, **kwargs):
        super(TestClient, self).__init__(coin='bitcoin_testnet3', *args, **kwargs)

    def on_handshake(self):
        print("Asking for: %s" % int(Block.objects.get(height=0).calculate_hash(), 16))
        self.send_message(messages.GetData(inventory=[structures.Inventory(
            inv_type=values.INVENTORY_TYPE["MSG_BLOCK"],
            inv_hash=int(Block.objects.get(height=0).calculate_hash(), 16),
        )]))

    def handle_block(self, header, block_message):
        print("Got block: %s" % block_message)
        for tx in block_message.txns:
            print(tx)

class Script(object):
    def __init__(self):
        self.datastack = []
        self.ifstack = []

    def run():
        pass
