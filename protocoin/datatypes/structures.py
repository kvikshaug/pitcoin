import hashlib
import time
import struct

from .meta import DataModel
from . import fields, values

class MessageHeader(DataModel):
    """The header of all bitcoin messages."""
    magic = fields.UInt32LEField(default=values.MAGIC_VALUES['bitcoin'])
    command = fields.FixedStringField(length=12, default=None)
    length = fields.UInt32LEField(default=0)
    checksum = fields.UInt32LEField(default=0)

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
    services = fields.UInt64LEField(default=values.SERVICES["NODE_NETWORK"])
    ip_address = fields.IPv4AddressField(default="0.0.0.0")
    port = fields.UInt16BEField(default=8333)

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
    timestamp = fields.UInt32LEField(default=lambda: time.time())
    address = IPv4Address()

    def __repr__(self):
        return "<%s Timestamp=[%s] Address=[%r]>" % \
            (self.__class__.__name__, time.ctime(self.timestamp), self.address)

class Inventory(DataModel):
    """The Inventory representation."""
    inv_type = fields.UInt32LEField(default=values.INVENTORY_TYPE["MSG_TX"])
    inv_hash = fields.Hash(default=0)

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
    out_hash = fields.Hash(default=0)
    index = fields.UInt32LEField(default=0)

    def __repr__(self):
        return "<%s Index=[%d] Hash=[%064x]>" % \
            (self.__class__.__name__, self.index, self.out_hash)

class TxIn(DataModel):
    """The transaction input representation."""
    previous_output = OutPoint()
    signature_script = fields.VariableStringField(default="Empty")
    sequence = fields.UInt32LEField(default=0)

    def __repr__(self):
        return "<%s Sequence=[%d]>" % (self.__class__.__name__, self.sequence)

class TxOut(DataModel):
    """The transaction output."""
    value = fields.Int64LEField(default=0)
    pk_script = fields.VariableStringField(default="Empty")

    def get_btc_value(self):
        return self.value//100000000 + self.value%100000000/100000000.0

    def __repr__(self):
        return "<%s Value=[%.8f]>" % (self.__class__.__name__,
            self.get_btc_value())
