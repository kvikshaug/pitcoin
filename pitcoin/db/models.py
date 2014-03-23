from django.db import models

from datatypes.messages import Block as PBlock

class Block(models.Model):
    #
    # Official block data
    # https://en.bitcoin.it/wiki/Protocol_specification#block
    #
    version = models.IntegerField()
    prev_hash = models.CharField(max_length=64)
    merkle_root = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    bits = models.BigIntegerField()
    nonce = models.BigIntegerField()

    #
    # Extra data
    #

    # Height is this blocks' current count in the blockchain
    height = models.IntegerField()

    # A direct reference to the previous block
    prev_block = models.ForeignKey('db.Block', null=True) # ONLY the genesis block can have NULL!

    def calculate_hash(self):
        """Use protocoins hash calculation"""
        return PBlock(
            version=self.version,
            prev_block_hash=self.prev_hash,
            merkle_root=self.merkle_root,
            timestamp=self.timestamp,
            bits=self.bits,
            nonce=self.nonce,
        ).calculate_hash()
