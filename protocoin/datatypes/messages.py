import time
import random
import sys
import inspect

from meta import DataModel
import structures, values, fields
from ..exceptions import UnknownCommand

class Version(DataModel):
    command = "version"

    def __init__(self, *args, **kwargs):
        self.version = fields.Int32LEField(default=values.PROTOCOL_VERSION)
        self.services = fields.UInt64LEField(default=values.SERVICES["NODE_NETWORK"])
        self.timestamp = fields.Int64LEField(default=time.time())
        self.addr_recv = structures.IPv4Address()
        self.addr_from = structures.IPv4Address()
        self.nonce = fields.UInt64LEField(default=random.randint(0, 2**32-1))
        self.user_agent = fields.VariableStringField(default="/Perone:0.0.1/")
        super(Version, self).__init__(*args, **kwargs)

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

    def __init__(self, *args, **kwargs):
        self.nonce = fields.UInt64LEField(default=random.randint(0, 2**32-1))
        super(Ping, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)

class Pong(DataModel):
    command = "pong"

    def __init__(self, *args, **kwargs):
        self.nonce = fields.UInt64LEField(default=random.randint(0, 2**32-1))
        super(Pong, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)

class InventoryVector(DataModel):
    command = "inv"

    def __init__(self, *args, **kwargs):
        self.inventory = fields.ListField(structures.Inventory, default=[])
        super(InventoryVector, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.inventory)

    def __iter__(self):
        return iter(self.inventory)

class AddressVector(DataModel):
    command = "addr"

    def __init__(self, *args, **kwargs):
        self.addresses = fields.ListField(structures.IPv4AddressTimestamp, default=[])
        super(AddressVector, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.addresses)

    def __iter__(self):
        return iter(self.addresses)

class GetData(DataModel):
    """GetData message command."""
    command = "getdata"

    def __init__(self, *args, **kwargs):
        self.inventory = fields.ListField(structures.Inventory, default=[])
        super(GetData, self).__init__(*args, **kwargs)

class NotFound(GetData):
    """NotFound command message."""
    command = "notfound"

    def __init__(self, *args, **kwargs):
        self.inventory = fields.ListField(structures.Inventory, default=[])
        super(NotFound, self).__init__(*args, **kwargs)

class Tx(DataModel):
    """The main transaction representation, this object will
    contain all the inputs and outputs of the transaction."""
    command = "tx"

    def __init__(self, *args, **kwargs):
        self.version = fields.UInt32LEField(default=0)
        self.tx_in = fields.ListField(structures.TxIn, default=[])
        self.tx_out = fields.ListField(structures.TxOut, default=[])
        self.lock_time = fields.UInt32LEField(default=0)
        super(Tx, self).__init__(*args, **kwargs)

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

class Block(structures.BlockHeader):
    """The block message. This message contains all the transactions present in the block."""
    command = "block"

    def __init__(self, *args, **kwargs):
        self.version = fields.UInt32LEField(default=0)
        self.prev_block = fields.Hash(default=0)
        self.merkle_root = fields.Hash(default=0)
        self.timestamp = fields.UInt32LEField(default=0)
        self.bits = fields.UInt32LEField(default=0)
        self.nonce = fields.UInt32LEField(default=0)
        self.txns = fields.ListField(Tx, default=[])
        super(Block, self).__init__(*args, **kwargs)

    def __len__(self):
        return len(self.txns)

    def __iter__(self):
        return __iter__(self.txns)

    def __repr__(self):
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Tx Count=[%d]>" % \
            (self.__class__.__name__, self.version, time.ctime(self.timestamp),
                self.nonce, self.calculate_hash(), len(self))

class HeaderVector(DataModel):
    """The header only vector."""
    command = "headers"

    def __init__(self, *args, **kwargs):
        self.headers = fields.ListField(structures.BlockHeader, default=[])
        super(HeaderVector, self).__init__(*args, **kwargs)

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

MESSAGES = {c.command: c for name, c in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(c) and issubclass(c, DataModel) and c is not DataModel}
def deserialize(command, stream):
    try:
        return MESSAGES[command](stream=stream)
    except IndexError:
        raise UnknownCommand("Unknown command: %s" % command)
