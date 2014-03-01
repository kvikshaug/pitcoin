import json

from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages, fields, values
from protocoin import util

from address import AddressBook

class SyncClient(BitcoinClient):
    def __init__(self, *args, **kwargs):
        super(SyncClient, self).__init__(coin='bitcoin_testnet3', *args, **kwargs)

    def on_handshake(self):
        """Send the initial GetBlocks after handshaking"""
        self.get_more_blocks()

    def handle_inv(self, header, message):
        """Request data for any inv - the block handling will sort out random invs"""
        self.last_expected_block = message.inventory[-1].inv_hash
        self.send_message(messages.GetData(inventory=message.inventory))

    def handle_block(self, header, block):
        """Verify and save new blocks"""
        # Calculate the current target
        current_height = len(Synchronizer.blocks)
        prev_block = Synchronizer.blocks[-1]
        target = util.bits_to_target(prev_block['bits'])

        # If testnet, don't use 20-minute-rule targets; iterate backwards to last proper target
        if Synchronizer.testnet:
            height = current_height
            while target == Synchronizer.max_target and height > 0 and height % Synchronizer.retarget_interval:
                height -= 1
                target = util.bits_to_target(Synchronizer.blocks[height]['bits'])

        if block.prev_block != prev_block['hash']:
            # TODO: Proper logging
            print("Rejecting block %s: The previous block hash (%s) differs from our latest block hash (%s)" %
                (block, block.prev_block, prev_block['hash']))
            return

        # Every 2016 blocks, recalculate the target based on the wanted timespan.
        # For all other blocks, the target remains equal to the previous target.
        if current_height % Synchronizer.retarget_interval == 0:
            last_retargeted_block = Synchronizer.blocks[-Synchronizer.retarget_interval]
            timespan = prev_block['timestamp'] - last_retargeted_block['timestamp']

            # Limit adjustment step
            if timespan > Synchronizer.target_timespan * 4:
                timespan = Synchronizer.target_timespan * 4
            elif timespan < Synchronizer.target_timespan / 4:
                timespan = Synchronizer.target_timespan / 4

            # Adjust the target
            target *= timespan
            target /= Synchronizer.target_timespan

            # Round the target with the packed representation
            target = util.bits_to_target(util.target_to_bits(target))

            # Never exceed the maximum target
            if target > Synchronizer.max_target:
                target = Synchronizer.max_target

        # 20 minute rule for testnet
        if Synchronizer.testnet:
            if current_height % Synchronizer.retarget_interval != 0 and block.timestamp - prev_block['timestamp'] > 1200:
                target = Synchronizer.max_target

        if not block.validate_proof_of_work(target):
            # TODO proper logging
            print("Block %s invalid: (%s)" % (current_height, target))
            return

        Synchronizer.blocks.append({
            'nonce': block.nonce,
            'hash': block.calculate_hash(),
            'timestamp': block.timestamp,
            'merkle_root': block.merkle_root,
            'version': block.version,
            'bits': block.bits
        })

        if block.calculate_hash() == self.last_expected_block:
            # Last hash of the expected invs - fetch more
            self.get_more_blocks()

    def handle_notfound(self, header, message):
        print(message)

    def get_more_blocks(self):
        self.send_message(messages.GetBlocks(
            block_locator_hashes=Synchronizer.get_locator_blocks(),
        ))

class Synchronizer(object):

    blocks_file = 'blocks.json'

    max_target = util.bits_to_target(values.HIGHEST_TARGET_BITS)
    target_timespan = 60 * 60 * 24 * 7 * 2 # We want 2016 blocks to take 2 weeks.
    retarget_interval = 2016 # Blocks

    # Use references to this field to track down any testnet specific clauses
    testnet = True

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
