import hashlib
import struct
from datetime import datetime

from .meta import Field, BitcoinSerializable
from . import fields, values

class MessageHeader(BitcoinSerializable):
    """The header of all bitcoin messages."""
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('magic', fields.UInt32LEField(), default=values.MAGIC_VALUES['bitcoin']),
            Field('command', fields.FixedStringField(length=12)),
            Field('length', fields.UInt32LEField(), default=0),
            Field('checksum', fields.UInt32LEField(), default=0),
        ]
        super().__init__(*args, **kwargs)

    def set_coin(self, coin):
        self.magic = values.MAGIC_VALUES[coin]

    def _magic_to_text(self):
        """Converts the magic value to a textual representation."""
        for k, v in values.MAGIC_VALUES.items():
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

class IPv4Address(BitcoinSerializable):
    """The IPv4 Address (without timestamp)."""
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('services', fields.UInt64LEField(), default=values.SERVICES["NODE_NETWORK"]),
            Field('ip_address', fields.IPv4AddressField(), default="0.0.0.0"),
            Field('port', fields.UInt16BEField(), default=8333),
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
        return "<%s IP=[%s:%d] Services=%r>" % (self.__class__.__name__, self.ip_address, self.port, services)

class IPv4AddressTimestamp(BitcoinSerializable):
    """The IPv4 Address with timestamp."""
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('timestamp', fields.DatetimeField(fields.UInt32LEField()), default=lambda: datetime.utcnow()),
            Field('address', IPv4Address()),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Timestamp=[%s] Address=[%r]>" % \
            (self.__class__.__name__, self.timestamp, self.address)

class Inventory(BitcoinSerializable):
    """The Inventory representation."""
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('inv_type', fields.UInt32LEField(), default=values.INVENTORY_TYPE["MSG_TX"]),
            Field('inv_hash', fields.Hash(), default="{:064x}".format(0)),
        ]
        super().__init__(*args, **kwargs)

    def type_to_text(self):
        """Converts the inventory type to text representation."""
        for k, v in values.INVENTORY_TYPE.items():
            if v == self.inv_type:
                return k
        return "Unknown Type"

    def __repr__(self):
        return "<%s Type=[%s] Hash=[%s]>" % \
            (self.__class__.__name__, self.type_to_text(), self.inv_hash)

class OutPoint(BitcoinSerializable):
    """The OutPoint of a transaction."""
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('out_hash', fields.Hash(), default="{:064x}".format(0)),
            Field('index', fields.UInt32LEField(), default=0),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Index=[%d] Hash=[%s]>" % \
            (self.__class__.__name__, self.index, self.out_hash)

class TxIn(BitcoinSerializable):
    """The transaction input representation."""
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('previous_output', OutPoint()),
            Field('signature_script', fields.VariableByteStringField(), default=b""),
            Field('sequence', fields.UInt32LEField(), default=0),
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s Sequence=[%d]>" % (self.__class__.__name__, self.sequence)

class TxOut(BitcoinSerializable):
    """The transaction output."""
    def __init__(self, *args, **kwargs):
        self._fields = [
            Field('value', fields.Int64LEField(), default=0),
            Field('pk_script', fields.VariableByteStringField(), default=b""),
        ]
        super().__init__(*args, **kwargs)

    def get_btc_value(self):
        return self.value//100000000 + self.value%100000000/100000000.0

    def __repr__(self):
        return "<%s Value=[%.8f]>" % (self.__class__.__name__,
            self.get_btc_value())
