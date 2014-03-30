import struct
import socket
import calendar
from datetime import datetime

from .meta import BitcoinSerializable
from . import values

class PrimaryField(object):
    def deserialize(self, stream):
        data = stream.read(struct.calcsize(self.datatype))
        return struct.unpack(self.datatype, data)[0]

    def serialize(self, stream, value):
        stream.write(struct.pack(self.datatype, value))

class Int32LEField(PrimaryField):
    """32-bit little-endian integer field."""
    datatype = "<i"

class UInt32LEField(PrimaryField):
    """32-bit little-endian unsigned integer field."""
    datatype = "<I"

class Int64LEField(PrimaryField):
    """64-bit little-endian integer field."""
    datatype = "<q"

class UInt64LEField(PrimaryField):
    """64-bit little-endian unsigned integer field."""
    datatype = "<Q"

class Int16LEField(PrimaryField):
    """16-bit little-endian integer field."""
    datatype = "<h"

class UInt16LEField(PrimaryField):
    """16-bit little-endian unsigned integer field."""
    datatype = "<H"

class UInt16BEField(PrimaryField):
    """16-bit big-endian unsigned integer field."""
    datatype = ">H"

class DatetimeField(object):
    """A UTC unix timestamp, represented with an integer of varying datatype"""
    def __init__(self, int_serializer):
        self.int_serializer = int_serializer

    def deserialize(self, stream):
        int_value = self.int_serializer.deserialize(stream)
        return datetime.utcfromtimestamp(int_value)

    def serialize(self, stream, value):
        int_value = calendar.timegm(value.utctimetuple())
        self.int_serializer.serialize(stream, int_value)

class FixedStringField(object):
    """A fixed length encoded string field."""
    def __init__(self, length):
        self.length = length

    def deserialize(self, stream):
        data = stream.read(self.length)
        value = data.split(b"\x00", 1)[0]
        return value[:self.length].decode(values.STRING_ENCODING)

    def serialize(self, stream, value):
        value = value.encode(values.STRING_ENCODING)
        stream.write(value[:self.length])
        stream.write(b"\x00" * (12 - len(value)))

class ListField(object):
    """A field used to serialize/deserialize a list of fields. """
    def __init__(self, serialization_class, *args, **kwargs):
        self.serialization_class = serialization_class
        super(ListField, self).__init__(*args, **kwargs)

    def deserialize(self, stream):
        length = VariableIntegerField().deserialize(stream)
        items = []
        for i in range(length):
            item = self.serialization_class()
            item.deserialize(stream)
            items.append(item)
        return items

    def serialize(self, stream, values):
        VariableIntegerField().serialize(stream, len(values))
        for value in values:
            if isinstance(value, BitcoinSerializable):
                # This is a serializable, let the value itself handle serialization
                value.serialize(stream)
            else:
                # A normal value, serialize with the specified serialization class
                serializer = self.serialization_class()
                serializer.serialize(stream, value)

class IPv4AddressField(object):
    """An IPv4 address field without timestamp and reserved IPv6 space."""
    reserved = b"\x00"*10 + b"\xff"*2

    def deserialize(self, stream):
        unused_reserved = stream.read(12)
        addr = stream.read(4)
        return socket.inet_ntoa(addr)

    def serialize(self, stream, value):
        stream.write(self.reserved)
        stream.write(socket.inet_aton(value))

class VariableIntegerField(object):
    """A variable size integer field."""
    def deserialize(self, stream):
        int_id_raw = stream.read(struct.calcsize("<B"))
        int_id = struct.unpack("<B", int_id_raw)[0]
        if int_id == 0xFD:
            int_id = struct.unpack("<H", stream.read(2))[0]
        elif int_id == 0xFE:
            int_id = struct.unpack("<I", stream.read(4))[0]
        elif int_id == 0xFF:
            int_id = struct.unpack("<Q", stream.read(8))[0]
        return int(int_id)

    def serialize(self, stream, value):
        if value < 0xFD:
            data = struct.pack("<B", value)
        elif value <= 0xFFFF:
            data = struct.pack("<B", 0xFD) + struct.pack("<H", value)
        elif value <= 0xFFFFFFFF:
            data = struct.pack("<B", 0xFE) + struct.pack("<I", value)
        else:
            data = struct.pack("<B", 0xFF) + struct.pack("<Q", value)
        stream.write(data)

class VariableByteStringField(object):
    """A variable length bytestring field."""
    def deserialize(self, stream):
        length = VariableIntegerField().deserialize(stream)
        return stream.read(length)

    def serialize(self, stream, value):
        VariableIntegerField().serialize(stream, len(value))
        stream.write(value)

class VariableStringField(object):
    """A variable length encoded string field."""
    def deserialize(self, stream):
        length = VariableIntegerField().deserialize(stream)
        return stream.read(length).decode(values.STRING_ENCODING)

    def serialize(self, stream, value):
        VariableIntegerField().serialize(stream, len(value))
        stream.write(value.encode(values.STRING_ENCODING))

class Hash(object):
    """A hash type field."""
    datatype = "<I"

    def deserialize(self, stream):
        data_size = struct.calcsize(self.datatype)
        intvalue = 0
        for i in range(8):
            data = stream.read(data_size)
            val = struct.unpack(self.datatype, data)[0]
            intvalue += val << (i * 32)
        return "{:064x}".format(intvalue)

    def serialize(self, stream, value):
        value = int(value, 16)
        for i in range(8):
            stream.write(struct.pack(self.datatype, value & 0xFFFFFFFF))
            value >>= 32
