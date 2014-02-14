import time
import random

import structures, values

class Version(object):
    """The version command."""
    command = "version"
    def __init__(self):
        self.version = values.PROTOCOL_VERSION
        self.services = values.SERVICES["NODE_NETWORK"]
        self.timestamp = time.time()
        self.addr_recv = structures.IPv4Address()
        self.addr_from = structures.IPv4Address()
        self.nonce = random.randint(0, 2**32-1)
        self.user_agent = "/Perone:0.0.1/"

class VerAck(object):
    """The version acknowledge (verack) command."""
    command = "verack"

class Ping(object):
    """The ping command, which should always be
    answered with a Pong."""
    command = "ping"
    def __init__(self):
        self.nonce = random.randint(0, 2**32-1)

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__,
            self.nonce)

class Pong(object):
    """The pong command, usually returned when
    a ping command arrives."""
    command = "pong"
    def __init__(self):
        self.nonce = random.randint(0, 2**32-1)

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__,
            self.nonce)

class InventoryVector(object):
    """A vector of inventories."""
    command = "inv"

    def __init__(self):
        self.inventory = []

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__,
            len(self))

    def __len__(self):
        return len(self.inventory)

    def __iter__(self):
        return iter(self.inventory)

class AddressVector(object):
    """A vector of addresses."""
    command = "addr"

    def __init__(self):
        self.addresses = []

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__,
            len(self))

    def __len__(self):
        return len(self.addresses)

    def __iter__(self):
        return iter(self.addresses)

class GetData(InventoryVector):
    """GetData message command."""
    command = "getdata"

class NotFound(GetData):
    """NotFound command message."""
    command = "notfound"

class Tx(object):
    """The main transaction representation, this object will
    contain all the inputs and outputs of the transaction."""
    command = "tx"

    def __init__(self):
        self.version = 0
        self.tx_in = []
        self.tx_out = []
        self.lock_time = 0

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
    """The block message. This message contains all the transactions
    present in the block."""
    command = "block"

    def __init__(self):
        self.version = 0
        self.prev_block = 0
        self.merkle_root = 0
        self.timestamp = 0
        self.bits = 0
        self.nonce = 0
        self.txns = []

    def __len__(self):
        return len(self.txns)

    def __iter__(self):
        return __iter__(self.txns)

    def __repr__(self):
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Tx Count=[%d]>" % \
            (self.__class__.__name__, self.version, time.ctime(self.timestamp),
                self.nonce, self.calculate_hash(), len(self))

class HeaderVector(object):
    """The header only vector."""
    command = "headers"

    def __init__(self):
        self.headers = []

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__,
            len(self))

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        return iter(self.headers)

class MemPool(object):
    """The mempool command."""
    command = "mempool"

class GetAddr(object):
    """The getaddr command."""
    command = "getaddr"
