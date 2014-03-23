from datetime import datetime

from net.clients import BitcoinClient
from datatypes import messages
from address import AddressBook
from db.models import Block
import validator

class SyncClient(BitcoinClient):
    def __init__(self, *args, **kwargs):
        from testnet import testnet
        if not testnet:
            super(SyncClient, self).__init__(*args, **kwargs)
        else:
            super(SyncClient, self).__init__(coin='bitcoin_testnet3', *args, **kwargs)

        # We'll keep a reference to the highest block for performance. Note that this means the
        # synchronization should never run in parallel with other processes that writes to the local
        # block chain.
        self.prev_block = Block.objects.order_by('height').last()

    def on_handshake(self):
        """Send the initial GetBlocks after handshaking"""
        self.get_more_blocks()

    def handle_inv(self, header, message):
        """Request data for any inv - the block handling will sort out random invs"""
        self.last_expected_block_hash = message.inventory[-1].inv_hash
        self.send_message(messages.GetData(inventory=message.inventory))

    def handle_block(self, header, block):
        """Validate and save new blocks"""
        if not validator.validate_block(block, self.prev_block):
            return

        # Save the new block
        block.prev_block = self.prev_block
        block.height = self.prev_block.height + 1
        block.save()
        self.prev_block = block

        if block.calculate_hash() == self.last_expected_block_hash:
            # Last hash of the expected invs - fetch more
            self.get_more_blocks()
            # Logic when we're done?

    def handle_notfound(self, header, message):
        print(message)

    def get_more_blocks(self):
        self.send_message(messages.GetBlocks(
            block_locator_hashes=Synchronizer.get_locator_blocks(self.prev_block),
        ))

class Synchronizer(object):
    @staticmethod
    def synchronize():
        # Test against as for now
        # node = AddressBook.get_node()
        client = SyncClient("as")
        client.handshake()
        client.loop()

    @staticmethod
    def get_locator_blocks(prev_block):
        """When catching up, in case the chain has diverged, use these hashes to detect the newest
        valid block in our local chain. See https://en.bitcoin.it/wiki/Protocol_specification#getblocks"""
        top = prev_block.height
        i = top
        step = 1
        hashes = []
        while i >= 0:
            hashes.append(Block.objects.get(height=i).calculate_hash())
            if i <= top - 10:
                step *= 2
            i -= step
        return hashes
