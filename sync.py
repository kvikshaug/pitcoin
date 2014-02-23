import json

from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages, fields

from address import AddressBook

class SyncClient(BitcoinClient):
    def __init__(self, *args, **kwargs):
        super(SyncClient, self).__init__(coin='bitcoin_testnet3', *args, **kwargs)
        self.inv_queue = []

    def on_handshake(self):
        self.send_message(messages.GetBlocks(
            block_locator_hashes=Synchronizer.get_locator_blocks(),
        ))

    def handle_block(self, header, message):
        print("Save block: %s" % message)

    def handle_inv(self, header, message):
        # Note: Need to differentiate between the one we asked for, and random invs?
        print("Got %s invs; asking for them" % len(message.inventory))
        self.inv_queue.extend(message.inventory)
        self.get_next()

    def handle_notfound(self, header, message):
        print(message)

    def get_next(self):
        self.send_message(messages.GetData(inventory=self.inv_queue))

class Synchronizer(object):

    blocks_file = 'blocks.json'

    @staticmethod
    def synchronize():
        # Read block data from disk
        with open(Synchronizer.blocks_file) as f:
            Synchronizer.blocks = json.loads(f.read())

        node = AddressBook.get_node()
        client = SyncClient(node.ip_address, node.port)
        client.handshake()
        client.loop()

    @staticmethod
    def get_locator_blocks():
        """When catching up, in case the chain has diverged, use these hashes to detect the newest
        valid block in our local chain"""
        i = len(Synchronizer.blocks) - 1
        ten_blocks_less = len(Synchronizer.blocks) - 10
        step = 1
        hashes = []
        while True:
            field = fields.Hash()
            field.set_value(Synchronizer.blocks[i]['hash'])
            hashes.append(field)
            if i <= ten_blocks_less:
                step *= 2
            i -= step
            if i < 0:
                break
        return hashes
