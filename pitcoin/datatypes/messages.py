import time
import random
from io import BytesIO
import binascii
import hashlib
from datetime import datetime

from util import compact
from .meta import Field, BitcoinSerializable
from . import structures, values, fields

class Version(BitcoinSerializable):
    command = "version"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('version', fields.Int32LEField(), default=values.PROTOCOL_VERSION),
            Field('services', fields.UInt64LEField(), default=values.SERVICES["NODE_NETWORK"]),
            Field('timestamp', fields.DatetimeField(fields.Int64LEField()), default=lambda: datetime.utcnow()),
            Field('addr_recv', structures.IPv4Address()),
            Field('addr_from', structures.IPv4Address()),
            Field('nonce', fields.UInt64LEField(), default=lambda: random.randint(0, 2**32-1)),
            Field('user_agent', fields.VariableStringField(), default="/Perone:0.0.1/"),
        ]
        super().__init__(*args, **kwargs)

    def _services_to_text(self):
        """Converts the services field into a textual
        representation."""
        services = []
        for service_name, flag_mask in values.SERVICES.items():
            if self.services & flag_mask:
                services.append(service_name)
        return services

    def __repr__(self):
        services = self._services_to_text()
        if not services:
            services = "No Services"
        return "<%s Version=[%d] Services=%r Timestamp=[%s] Recv=[%r] From=[%r] Nonce=[%d] UA=[%s]>" % \
            (self.__class__.__name__, self.version, services, self.timestamp, self.addr_recv, self.addr_from,
            self.nonce, self.user_agent)

class VerAck(BitcoinSerializable):
    """The version acknowledge (verack) command."""
    command = "verack"
    def __init__(self, *args, **kwargs):
        self._fields = []
        super().__init__(*args, **kwargs)

class Ping(BitcoinSerializable):
    command = "ping"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('nonce', fields.UInt64LEField(), default=lambda: random.randint(0, 2**32-1)),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)

class Pong(BitcoinSerializable):
    command = "pong"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('nonce', fields.UInt64LEField(), default=lambda: random.randint(0, 2**32-1)),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)

class InventoryVector(BitcoinSerializable):
    command = "inv"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('inventory', fields.ListField(structures.Inventory), default=[]),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.inventory)

    def __iter__(self):
        return iter(self.inventory)

class AddressVector(BitcoinSerializable):
    command = "addr"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('addresses', fields.ListField(structures.IPv4AddressTimestamp), default=[]),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.addresses)

    def __iter__(self):
        return iter(self.addresses)

class GetData(BitcoinSerializable):
    command = "getdata"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('inventory', fields.ListField(structures.Inventory), default=[]),
        ]
        super().__init__(*args, **kwargs)

class NotFound(BitcoinSerializable):
    command = "notfound"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('inventory', fields.ListField(structures.Inventory), default=[]),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Inv Count[%d]>" % (self.__class__.__name__, len(self.inventory))

class Tx(BitcoinSerializable):
    """The main transaction representation, this object will contain all the inputs and outputs of the transaction."""
    command = "tx"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('version', fields.UInt32LEField(), default=0),
            Field('tx_in', fields.ListField(structures.TxIn), default=[]),
            Field('tx_out', fields.ListField(structures.TxOut), default=[]),
            Field('lock_time', fields.UInt32LEField(), default=0),
        ]
        super().__init__(*args, **kwargs)

    def _locktime_to_text(self):
        """Converts the lock-time to textual representation."""
        text = "Unknown"
        if self.lock_time == 0:
            text = "Always Locked"
        elif self.lock_time < 500000000:
            text = "Block %d" % self.lock_time
        elif self.lock_time >= 500000000:
            text = time.ctime(self.lock_time)
        return text

    def __repr__(self):
        return "<%s Version=[%d] Lock Time=[%s] TxIn Count=[%d] TxOut Count=[%d]>" \
            % (self.__class__.__name__, self.version, self._locktime_to_text(),
                len(self.tx_in), len(self.tx_out))

class Block(BitcoinSerializable):
    """The block message. This message contains all the transactions present in the block."""
    command = "block"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('version', fields.UInt32LEField(), default=0),
            Field('prev_block_hash', fields.Hash(), default="{:064x}".format(0)),
            Field('merkle_root', fields.Hash(), default="{:064x}".format(0)),
            Field('timestamp', fields.DatetimeField(fields.UInt32LEField()), default=lambda: datetime.utcnow()),
            Field('bits', fields.UInt32LEField(), default=0),
            Field('nonce', fields.UInt32LEField(), default=0),
            Field('txns', fields.ListField(Tx), default=[]),
        ]
        super().__init__(*args, **kwargs)

    def __len__(self):
        return len(self.txns)

    def __iter__(self):
        return __iter__(self.txns)

    def calculate_hash(self):
        hash_fields = [f for f in self._fields if f.name != 'txns']
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
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Tx Count=[%d]>" % \
            (self.__class__.__name__, self.version, self.timestamp, self.nonce, self.calculate_hash(), len(self.txns))

class HeaderVector(BitcoinSerializable):
    """The header only vector."""
    command = "headers"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('headers', fields.ListField(Block), default=[]),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        return iter(self.headers)

class MemPool(BitcoinSerializable):
    command = "mempool"
    def __init__(self, *args, **kwargs):
        self._fields = []
        super().__init__(*args, **kwargs)

class GetAddr(BitcoinSerializable):
    command = "getaddr"
    def __init__(self, *args, **kwargs):
        self._fields = []
        super().__init__(*args, **kwargs)

class GetBlocks(BitcoinSerializable):
    command = "getblocks"
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('version', fields.UInt32LEField(), values.PROTOCOL_VERSION),
            Field('block_locator_hashes', fields.ListField(fields.Hash), default=[]),
            Field('hash_stop', fields.Hash(), default="{:064x}".format(0)),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Version=[%d] HashCount=[%d]>" % \
            (self.__class__.__name__, self.version, len(self.block_locator_hashes))
