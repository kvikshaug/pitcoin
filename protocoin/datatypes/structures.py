import hashlib
import time
import struct

from meta import DataModel
import fields, values

class MessageHeader(DataModel):
    """The header of all bitcoin messages."""

    def __init__(self, *args, **kwargs):
        self.magic = fields.UInt32LEField(default=values.MAGIC_VALUES['bitcoin'])
        self.command = fields.FixedStringField(length=12, default=None)
        self.length = fields.UInt32LEField(default=0)
        self.checksum = fields.UInt32LEField(default=0)
        super(MessageHeader, self).__init__(*args, **kwargs)

    def set_coin(self, coin):
        self.magic = values.MAGIC_VALUES[coin]

    def _magic_to_text(self):
        """Converts the magic value to a textual representation."""
        for k, v in values.MAGIC_VALUES.iteritems():
            if v == self.magic:
                return k
        return "Unknown Magic"

    def __repr__(self):
        return "<%s Magic=[%s] Command=[%s] Length=[%d] Checksum=[%d]>" % \
            (self.__class__.__name__, self._magic_to_text(), self.command, self.length, self.checksum)

    @staticmethod
    def calcsize():
        return struct.calcsize("i12sii")

    @staticmethod
    def calc_checksum(payload):
        """Calculate the checksum of the specified payload.

        :param payload: The binary data payload.
        """
        sha256hash = hashlib.sha256(payload)
        sha256hash = hashlib.sha256(sha256hash.digest())
        checksum = sha256hash.digest()[:4]
        return struct.unpack("<I", checksum)[0]

class IPv4Address(DataModel):
    """The IPv4 Address (without timestamp)."""

    def __init__(self, *args, **kwargs):
        self.services = fields.UInt64LEField(default=values.SERVICES["NODE_NETWORK"])
        self.ip_address = fields.IPv4AddressField(default="0.0.0.0")
        self.port = fields.UInt16BEField(default=8333)
        super(IPv4Address, self).__init__(*args, **kwargs)

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
        return "<%s IP=[%s:%d] Services=%r>" % (self.__class__.__name__, self.ip_address, self.port, services)

class IPv4AddressTimestamp(DataModel):
    """The IPv4 Address with timestamp."""

    def __init__(self, *args, **kwargs):
        self.timestamp = fields.UInt32LEField(default=time.time())
        self.address = IPv4Address()
        super(DataModel, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Timestamp=[%s] Address=[%r]>" % \
            (self.__class__.__name__, time.ctime(self.timestamp), self.address)

class Inventory(DataModel):
    """The Inventory representation."""

    def __init__(self, *args, **kwargs):
        self.inv_type = fields.UInt32LEField(default=values.INVENTORY_TYPE["MSG_TX"])
        self.inv_hash = fields.Hash(default=0)
        super(Inventory, self).__init__(*args, **kwargs)

    def type_to_text(self):
        """Converts the inventory type to text representation."""
        for k, v in values.INVENTORY_TYPE.iteritems():
            if v == self.inv_type:
                return k
        return "Unknown Type"

    def __repr__(self):
        return "<%s Type=[%s] Hash=[%064x]>" % \
            (self.__class__.__name__, self.type_to_text(), self.inv_hash)

class OutPoint(DataModel):
    """The OutPoint of a transaction."""

    def __init__(self, *args, **kwargs):
        self.out_hash = fields.Hash(default=0)
        self.index = fields.UInt32LEField(default=0)
        super(OutPoint, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Index=[%d] Hash=[%064x]>" % \
            (self.__class__.__name__, self.index, self.out_hash)

class TxIn(DataModel):
    """The transaction input representation."""

    def __init__(self, *args, **kwargs):
        self.previous_output = OutPoint()
        self.signature_script = fields.VariableStringField(default="Empty")
        self.sequence = fields.UInt32LEField(default=0)
        super(TxIn, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Sequence=[%d]>" % (self.__class__.__name__, self.sequence)

class TxOut(DataModel):
    """The transaction output."""

    def __init__(self, *args, **kwargs):
        self.value = fields.Int64LEField(default=0)
        self.pk_script = fields.VariableStringField(default="Empty")
        super(TxOut, self).__init__(*args, **kwargs)

    def get_btc_value(self):
        return self.value//100000000 + self.value%100000000/100000000.0

    def __repr__(self):
        return "<%s Value=[%.8f]>" % (self.__class__.__name__,
            self.get_btc_value())
