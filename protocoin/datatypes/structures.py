import hashlib
import time

import values

class MessageHeader(object):
    """The header of all bitcoin messages."""
    def __init__(self, coin="bitcoin"):
        self.magic = values.MAGIC_VALUES[coin]
        self.command = "None"
        self.length = 0
        self.checksum = 0

    def _magic_to_text(self):
        """Converts the magic value to a textual representation."""
        for k, v in values.MAGIC_VALUES.iteritems():
            if v == self.magic:
                return k
        return "Unknown Magic"

    def __repr__(self):
        return "<%s Magic=[%s] Length=[%d] Checksum=[%d]>" % \
            (self.__class__.__name__, self._magic_to_text(),
                self.length, self.checksum)

class IPv4Address(object):
    """The IPv4 Address (without timestamp)."""
    def __init__(self):
        self.services = values.SERVICES["NODE_NETWORK"]
        self.ip_address = "0.0.0.0"
        self.port = 8333

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
        return "<%s IP=[%s:%d] Services=%r>" % (self.__class__.__name__,
            self.ip_address, self.port, services)

class IPv4AddressTimestamp(IPv4Address):
    """The IPv4 Address with timestamp."""
    def __init__(self):
        super(IPv4AddressTimestamp, self).__init__()
        self.timestamp = time.time()

    def __repr__(self):
        services = self._services_to_text()
        if not services:
            services = "No Services"
        return "<%s Timestamp=[%s] IP=[%s:%d] Services=%r>" % \
            (self.__class__.__name__, time.ctime(self.timestamp),
                self.ip_address, self.port, services)

class Inventory(object):
    """The Inventory representation."""
    def __init__(self):
        self.inv_type = values.INVENTORY_TYPE["MSG_TX"]
        self.inv_hash = 0

    def type_to_text(self):
        """Converts the inventory type to text representation."""
        for k, v in values.INVENTORY_TYPE.iteritems():
            if v == self.inv_type:
                return k
        return "Unknown Type"

    def __repr__(self):
        return "<%s Type=[%s] Hash=[%064x]>" % \
            (self.__class__.__name__, self.type_to_text(),
                self.inv_hash)

class OutPoint(object):
    """The OutPoint of a transaction."""
    def __init__(self):
        self.out_hash = 0
        self.index = 0

    def __repr__(self):
        return "<%s Index=[%d] Hash=[%064x]>" % \
            (self.__class__.__name__, self.index,
                self.out_hash)

class TxIn(object):
    """The transaction input representation."""
    def __init__(self):
        self.previous_output = None
        self.signature_script = "Empty"
        self.sequence = 0

    def __repr__(self):
        return "<%s Sequence=[%d]>" % \
            (self.__class__.__name__, self.sequence)

class TxOut(object):
    """The transaction output."""
    def __init__(self):
        self.value = 0
        self.pk_script = "Empty"

    def get_btc_value(self):
        return self.value//100000000 + self.value%100000000/100000000.0

    def __repr__(self):
        return "<%s Value=[%.8f]>" % (self.__class__.__name__,
            self.get_btc_value())

class BlockHeader(object):
    """The header of the block."""
    def __init__(self):
        self.version = 0
        self.prev_block = 0
        self.merkle_root = 0
        self.timestamp = 0
        self.bits = 0
        self.nonce = 0
        self.txns_count = 0

    def calculate_hash(self):
        """This method will calculate the hash of the block."""
        hash_fields = ["version", "prev_block", "merkle_root",
            "timestamp", "bits", "nonce"]
        from .serializers import BlockSerializer
        serializer = BlockSerializer()
        bin_data = serializer.serialize(self, hash_fields)
        h = hashlib.sha256(bin_data).digest()
        h = hashlib.sha256(h).digest()
        return h[::-1].encode("hex_codec")

    def __repr__(self):
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Tx Count=[%d]>" % \
            (self.__class__.__name__, self.version, time.ctime(self.timestamp),
                self.nonce, self.calculate_hash(), self.txns_count)
