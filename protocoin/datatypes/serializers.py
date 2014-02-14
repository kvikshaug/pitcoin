import hashlib
import struct
from cStringIO import StringIO
from collections import OrderedDict

import messages, structures, fields
from ..exceptions import UnknownCommand

class SerializerMeta(type):
    """The serializer meta class. This class will create an attribute
    called '_fields' in each serializer with the ordered dict of
    fields present on the subclasses.
    """
    def __new__(meta, name, bases, attrs):
        attrs["_fields"] = meta.get_fields(bases, attrs, fields.Field)
        return super(SerializerMeta, meta).__new__(meta, name, bases, attrs)

    @classmethod
    def get_fields(meta, bases, attrs, field_class):
        """This method will construct an ordered dict with all
        the fields present on the serializer classes."""
        fields = [(field_name, attrs.pop(field_name))
            for field_name, field_value in list(attrs.iteritems())
            if isinstance(field_value, field_class)]

        for base_cls in bases[::-1]:
            if hasattr(base_cls, "_fields"):
                fields = list(base_cls._fields.items()) + fields

        fields.sort(key=lambda it: it[1].count)
        return OrderedDict(fields)

class SerializerABC(object):
    """The serializer abstract base class."""
    __metaclass__ = SerializerMeta

class Serializer(SerializerABC):
    """The main serializer class, inherit from this class to
    create custom serializers.

    Example of use::

        class VerAckSerializer(Serializer):
            model_class = VerAck
    """
    def serialize(self, obj, fields=None):
        """This method will receive an object and then will serialize
        it according to the fields declared on the serializer.

        :param obj: The object to serializer.
        """
        bin_data = StringIO()
        for field_name, field_obj in self._fields.iteritems():
            if fields:
                if field_name not in fields:
                    continue
            attr = getattr(obj, field_name, None)
            field_obj.parse(attr)
            bin_data.write(field_obj.serialize())

        return bin_data.getvalue()

    def deserialize(self, stream):
        """This method will read the stream and then will deserialize the
        binary data information present on it.

        :param stream: A file-like object (StringIO, file, socket, etc.)
        """
        model = self.model_class()
        for field_name, field_obj in self._fields.iteritems():
            value = field_obj.deserialize(stream)
            setattr(model, field_name, value)
        return model

class MessageHeaderSerializer(Serializer):
    """Serializer for the MessageHeader."""
    model_class = structures.MessageHeader
    magic = fields.UInt32LEField()
    command = fields.FixedStringField(12)
    length = fields.UInt32LEField()
    checksum = fields.UInt32LEField()

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

class IPv4AddressSerializer(Serializer):
    """Serializer for the IPv4Address."""
    model_class = structures.IPv4Address
    services = fields.UInt64LEField()
    ip_address = fields.IPv4AddressField()
    port = fields.UInt16BEField()

class IPv4AddressTimestampSerializer(Serializer):
    """Serializer for the IPv4AddressTimestamp."""
    model_class = structures.IPv4AddressTimestamp
    timestamp = fields.UInt32LEField()
    services = fields.UInt64LEField()
    ip_address = fields.IPv4AddressField()
    port = fields.UInt16BEField()

class VersionSerializer(Serializer):
    """The version command serializer."""
    model_class = messages.Version
    version = fields.Int32LEField()
    services = fields.UInt64LEField()
    timestamp = fields.Int64LEField()
    addr_recv = fields.NestedField(IPv4AddressSerializer)
    addr_from = fields.NestedField(IPv4AddressSerializer)
    nonce = fields.UInt64LEField()
    user_agent = fields.VariableStringField()

class VerAckSerializer(Serializer):
    """The serializer for the verack command."""
    model_class = messages.VerAck

class PingSerializer(Serializer):
    """The ping command serializer."""
    model_class = messages.Ping
    nonce = fields.UInt64LEField()

class PongSerializer(Serializer):
    """The pong command serializer."""
    model_class = messages.Pong
    nonce = fields.UInt64LEField()

class InventorySerializer(Serializer):
    """The serializer for the Inventory."""
    model_class = structures.Inventory
    inv_type = fields.UInt32LEField()
    inv_hash = fields.Hash()

class InventoryVectorSerializer(Serializer):
    """The serializer for the vector of inventories."""
    model_class = messages.InventoryVector
    inventory = fields.ListField(InventorySerializer)

class AddressVectorSerializer(Serializer):
    """Serializer for the addresses vector."""
    model_class = messages.AddressVector
    addresses = fields.ListField(IPv4AddressTimestampSerializer)

class GetDataSerializer(Serializer):
    """Serializer for the GetData command."""
    model_class = messages.GetData
    inventory = fields.ListField(InventorySerializer)

class NotFoundSerializer(Serializer):
    """Serializer for the NotFound message."""
    model_class = messages.NotFound
    inventory = fields.ListField(InventorySerializer)

class OutPointSerializer(Serializer):
    """The OutPoint representation serializer."""
    model_class = structures.OutPoint
    out_hash = fields.Hash()
    index = fields.UInt32LEField()

class TxInSerializer(Serializer):
    """The transaction input serializer."""
    model_class = structures.TxIn
    previous_output = fields.NestedField(OutPointSerializer)
    signature_script = fields.VariableStringField()
    sequence = fields.UInt32LEField()

class TxOutSerializer(Serializer):
    """The transaction output serializer."""
    model_class = structures.TxOut
    value = fields.Int64LEField()
    pk_script = fields.VariableStringField()

class TxSerializer(Serializer):
    """The transaction serializer."""
    model_class = messages.Tx
    version = fields.UInt32LEField()
    tx_in = fields.ListField(TxInSerializer)
    tx_out = fields.ListField(TxOutSerializer)
    lock_time = fields.UInt32LEField()

class BlockHeaderSerializer(Serializer):
    """The serializer for the block header."""
    model_class = structures.BlockHeader
    version = fields.UInt32LEField()
    prev_block = fields.Hash()
    merkle_root = fields.Hash()
    timestamp = fields.UInt32LEField()
    bits = fields.UInt32LEField()
    nonce = fields.UInt32LEField()
    txns_count = fields.VariableIntegerField()

class BlockSerializer(Serializer):
    """The deserializer for the blocks."""
    model_class = messages.Block
    version = fields.UInt32LEField()
    prev_block = fields.Hash()
    merkle_root = fields.Hash()
    timestamp = fields.UInt32LEField()
    bits = fields.UInt32LEField()
    nonce = fields.UInt32LEField()
    txns = fields.ListField(TxSerializer)

class HeaderVectorSerializer(Serializer):
    """Serializer for the block header vector."""
    model_class = messages.HeaderVector
    headers = fields.ListField(BlockHeaderSerializer)

class MemPoolSerializer(Serializer):
    """The serializer for the mempool command."""
    model_class = messages.MemPool

class GetAddrSerializer(Serializer):
    """The serializer for the getaddr command."""
    model_class = messages.GetAddr

MESSAGE_MAPPING = [
    ('version', VersionSerializer),
    ('verack', VerAckSerializer),
    ('ping', PingSerializer),
    ('pong', PongSerializer),
    ('inv', InventoryVectorSerializer),
    ('addr', AddressVectorSerializer),
    ('getdata', GetDataSerializer),
    ('notfound', NotFoundSerializer),
    ('tx', TxSerializer),
    ('block', BlockSerializer),
    ('headers', HeaderVectorSerializer),
    ('mempool', MemPoolSerializer),
    ('getaddr', GetAddrSerializer),
]

def get(command):
    matches = [m[1]() for m in MESSAGE_MAPPING if m[0] == command]
    if len(matches) != 1:
        raise UnknownCommand("Unknown command: %s" % command)
    return matches[0]
