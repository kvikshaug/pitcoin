from datetime import datetime

from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages, fields

from address import AddressBook
from db.models import Block
import validator

class SyncClient(BitcoinClient):
    def __init__(self, *args, **kwargs):
        from client import testnet
        if not testnet:
            super(SyncClient, self).__init__(*args, **kwargs)
        else:
            super(SyncClient, self).__init__(coin='bitcoin_testnet3', *args, **kwargs)

    def on_handshake(self):
        """Send the initial GetBlocks after handshaking"""
        self.get_more_blocks()

    def handle_inv(self, header, message):
        """Request data for any inv - the block handling will sort out random invs"""
        self.last_expected_block_hash = "{:064x}".format(message.inventory[-1].inv_hash)
        self.send_message(messages.GetData(inventory=message.inventory))

    def handle_block(self, header, block_message):
        """Validate and save new blocks"""
        if not validator.validate_block(block_message):
            return

        # Save the new block
        prev_block = Block.objects.order_by('height').last()
        block = Block(
            version=block_message.version,
            prev_hash=block_message.prev_hash(),
            merkle_root="{:064x}".format(block_message.merkle_root),
            timestamp=datetime.utcfromtimestamp(block_message.timestamp),
            bits=block_message.bits,
            nonce=block_message.nonce,
            prev_block=prev_block,
            height=prev_block.height + 1,
        )
        block.save()

        if block_message.calculate_hash() == self.last_expected_block_hash:
            # Last hash of the expected invs - fetch more
            self.get_more_blocks()
            # Logic when we're done?

    def handle_notfound(self, header, message):
        print(message)

    def get_more_blocks(self):
        self.send_message(messages.GetBlocks(
            block_locator_hashes=Synchronizer.get_locator_blocks(),
        ))

class Synchronizer(object):
    @staticmethod
    def synchronize():
        node = AddressBook.get_node()
        client = SyncClient(node.ip_address, node.port)
        client.handshake()
        client.loop()

    @staticmethod
    def get_locator_blocks():
        """When catching up, in case the chain has diverged, use these hashes to detect the newest
        valid block in our local chain. See https://en.bitcoin.it/wiki/Protocol_specification#getblocks"""
        top = Block.objects.order_by('height').last().height
        i = top
        step = 1
        hashes = []
        while i >= 0:
            field = fields.Hash()
            field.set_value(int(Block.objects.get(height=i).calculate_hash(), 16))
            hashes.append(field)
            if i <= top - 10:
                step *= 2
            i -= step
        return hashes
