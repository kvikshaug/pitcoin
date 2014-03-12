from django.db import models

class Block(models.Model):
    #
    # Official block data
    # https://en.bitcoin.it/wiki/Protocol_specification#block
    #
    version = models.IntegerField()
    prev_hash = models.CharField(max_length=64)
    merkle_root = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    bits = models.IntegerField()
    nonce = models.IntegerField()

    #
    # Extra data
    #

    # Height is this blocks' current count in the blockchain
    height = models.IntegerField()

    # A direct reference to the previous block
    prev_block = models.ForeignKey('db.Block', null=True) # ONLY the genesis block can have NULL!
