import time
import random
import sys
import inspect
from io import BytesIO
import binascii
import hashlib

from meta import DataModel
import structures, values, fields
from ..exceptions import UnknownCommand

class Version(DataModel):
    command = "version"
    version = fields.Int32LEField(default=values.PROTOCOL_VERSION)
    services = fields.UInt64LEField(default=values.SERVICES["NODE_NETWORK"])
    timestamp = fields.Int64LEField(default=lambda: time.time())
    addr_recv = structures.IPv4Address()
    addr_from = structures.IPv4Address()
    nonce = fields.UInt64LEField(default=lambda: random.randint(0, 2**32-1))
    user_agent = fields.VariableStringField(default="/Perone:0.0.1/")

    def _services_to_text(self):
        """Converts the services field into a textual
        representation."""
        services = []
        for service_name, flag_mask in values.SERVICES.iteritems():
            if self.services & flag_mask:
                services.append(service_name)
        return services

    def __repr__(self):
        services = self._services_to_text()
        if not services:
            services = "No Services"
        return "<%s Version=[%d] Services=%r Timestamp=[%s] Recv=[%r] From=[%r] Nonce=[%d] UA=[%s]>" % \
            (self.__class__.__name__, self.version, services, time.ctime(self.timestamp), self.addr_recv,
            self.addr_from, self.nonce, self.user_agent)

class VerAck(DataModel):
    """The version acknowledge (verack) command."""
    command = "verack"

class Ping(DataModel):
    command = "ping"
    nonce = fields.UInt64LEField(default=lambda: random.randint(0, 2**32-1))

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)

class Pong(DataModel):
    command = "pong"
    nonce = fields.UInt64LEField(default=lambda: random.randint(0, 2**32-1))

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)

class InventoryVector(DataModel):
    command = "inv"
    inventory = fields.ListField(structures.Inventory)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.inventory)

    def __iter__(self):
        return iter(self.inventory)

class AddressVector(DataModel):
    command = "addr"
    addresses = fields.ListField(structures.IPv4AddressTimestamp)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.addresses)

    def __iter__(self):
        return iter(self.addresses)

class GetData(DataModel):
    command = "getdata"
    inventory = fields.ListField(structures.Inventory)

class NotFound(GetData):
    """NotFound command message."""
    command = "notfound"
    inventory = fields.ListField(structures.Inventory)

    def __repr__(self):
        return "<%s Inv Count[%d]>" % (self.__class__.__name__, len(self.inventory))

class Tx(DataModel):
    """The main transaction representation, this object will
    contain all the inputs and outputs of the transaction."""
    command = "tx"
    version = fields.UInt32LEField(default=0)
    tx_in = fields.ListField(structures.TxIn)
    tx_out = fields.ListField(structures.TxOut)
    lock_time = fields.UInt32LEField(default=0)

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

class Block(DataModel):
    """The block message. This message contains all the transactions present in the block."""
    command = "block"
    version = fields.UInt32LEField(default=0)
    prev_block = fields.Hash(default=0)
    merkle_root = fields.Hash(default=0)
    timestamp = fields.UInt32LEField(default=0)
    bits = fields.UInt32LEField(default=0)
    nonce = fields.UInt32LEField(default=0)
    txns = fields.ListField(Tx)

    def __len__(self):
        return len(self.txns)

    def __iter__(self):
        return __iter__(self.txns)

    def calculate_hash(self):
        hash_fields = ["version", "prev_block", "merkle_root", "timestamp", "bits", "nonce"]
        stream = BytesIO()
        for field_name in hash_fields:
            self._fields[field_name].serialize(stream)
        h = hashlib.sha256(stream.getvalue()).digest()
        h = hashlib.sha256(h).digest()
        return binascii.hexlify(h[::-1])

    def calculate_claimed_target(self):
        """Calculates the target based on the claimed difficulty bits, which should normally not be trusted"""
        h = hex(self.bits)[2:]
        c1, c2 = int(h[:2], 16), int(h[2:], 16)
        return c2 * 2 ** (8 * (c1 - 3))

    def validate_claimed_proof_of_work(self):
        """Validate proof of work based on the difficulty claimed by the block creator"""
        return self.validate_proof_of_work(self.calculate_claimed_target())

    def validate_proof_of_work(self, target):
        """Validate proof of work based on the given difficulty"""
        return int(self.calculate_hash(), 16) <= target

    def __repr__(self):
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Tx Count=[%d]>" % \
            (self.__class__.__name__, self.version, time.ctime(self.timestamp), self.nonce,
            self.calculate_hash(), len(self.txns))

class HeaderVector(DataModel):
    """The header only vector."""
    command = "headers"
    headers = fields.ListField(Block)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        return iter(self.headers)

class MemPool(DataModel):
    """The mempool command."""
    command = "mempool"

class GetAddr(DataModel):
    """The getaddr command."""
    command = "getaddr"

class GetBlocks(DataModel):
    command = "getblocks"
    version = fields.UInt32LEField(default=values.PROTOCOL_VERSION)
    block_locator_hashes = fields.ListField(fields.Hash)
    hash_stop = fields.Hash(default=0)

    def __repr__(self):
        return "<%s Version=[%d] HashCount=[%d]>" % \
            (self.__class__.__name__, self.version, self.hash_count)

MESSAGES = {c.command: c for name, c in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(c) and issubclass(c, DataModel) and c is not DataModel}
def deserialize(command, stream):
    try:
        return MESSAGES[command](stream=stream)
    except IndexError:
        raise UnknownCommand("Unknown command: %s" % command)
