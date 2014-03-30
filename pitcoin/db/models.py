from datetime import datetime
from io import BytesIO
import hashlib
import binascii

from django.db import models

from datatypes.messages import Transaction
from datatypes.meta import Field, BitcoinSerializable
from datatypes import fields
from util import compact

class Block(BitcoinSerializable, models.Model):
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
    # Extra db data
    #

    # Height is this blocks' current count in the blockchain
    height = models.IntegerField()

    # A direct reference to the previous block
    prev_block = models.ForeignKey('db.Block', null=True) # ONLY the genesis block can have NULL!

    #
    # Serialization-data
    #

    command = "block"

    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('version', fields.UInt32LEField(), default=0),
            Field('prev_hash', fields.Hash()),
            Field('merkle_root', fields.Hash()),
            Field('timestamp', fields.DatetimeField(fields.UInt32LEField()), default=lambda: datetime.utcnow()),
            Field('bits', fields.UInt32LEField(), default=0),
            Field('nonce', fields.UInt32LEField(), default=0),
            Field('transactions', fields.ListField(Transaction), default=[]),
        ]
        super().__init__(*args, **kwargs)

    #
    # Other methods
    #

    def calculate_hash(self):
        hash_fields = [f for f in self._fields if f.name != 'transactions']
        stream = BytesIO()
        for field in hash_fields:
            field.serializer.serialize(stream, getattr(self, field.name))
        h = hashlib.sha256(stream.getvalue()).digest()
        h = hashlib.sha256(h).digest()
        return binascii.hexlify(h[::-1]).decode('ascii')

    def calculate_claimed_target(self):
        """Calculates the target based on the claimed difficulty bits, which should normally not be trusted"""
        return compact.bits_to_target(self.bits)

    def validate_claimed_proof_of_work(self):
        """Validate proof of work based on the difficulty claimed by the block creator"""
        return self.validate_proof_of_work(self.calculate_claimed_target())

    def validate_proof_of_work(self, target):
        """Validate proof of work based on the given difficulty"""
        return int(self.calculate_hash(), 16) <= target

    def __repr__(self):
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Transaction Count=[%d]>" % \
            (self.__class__.__name__, self.version, self.timestamp, self.nonce, self.calculate_hash(), len(self.transactions))
