import struct
import socket

class Field(object):
    order = 0

    def __init__(self, default=None):
        # Set the field order, which is used for serializing
        self.order = Field.order
        Field.order += 1

        # Save the default field value, which may be an actual value or a callable
        self.default = default
        self.set_value(self.get_default())

    def get_default(self):
        if callable(self.default):
            return self.default()
        else:
            return self.default

    def set_value(self, value):
        """Set the value directly"""
        raise NotImplemented

    def get_value(self):
        """Return the current value"""
        raise NotImplemented

    def deserialize(self, stream):
        """Deserialize the given stream into this field"""
        raise NotImplemented

    def serialize(self, stream):
        """Serialize the current value into the given stream"""
        raise NotImplemented

    def __repr__(self):
        return "<%s [%r]>" % (self.__class__.__name__, repr(self.value))

    def __str__(self):
        return str(self.value)


class PrimaryField(Field):
    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def deserialize(self, stream):
        data_size = struct.calcsize(self.datatype)
        data = stream.read(data_size)
        self.value = struct.unpack(self.datatype, data)[0]

    def serialize(self, stream):
        data = struct.pack(self.datatype, self.value)
        stream.write(data)

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

class FixedStringField(Field):
    """A fixed length string field."""
    def __init__(self, length, *args, **kwargs):
        self.length = length
        super(FixedStringField, self).__init__(*args, **kwargs)

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def deserialize(self, stream):
        data = stream.read(self.length)
        value = data.split("\x00", 1)[0]
        self.value = value[:self.length]

    def serialize(self, stream):
        stream.write(self.value[:self.length])
        stream.write("\x00" * (12 - len(self.value)))

class ListField(Field):
    """A field used to serialize/deserialize a list of fields. """
    def __init__(self, field_class, *args, **kwargs):
        self.length = VariableIntegerField()
        self.field_class = field_class
        super(ListField, self).__init__(default=[], *args, **kwargs)

    def set_value(self, value):
        self.length.set_value(len(value))
        self.value = value

    def get_value(self):
        return self.value

    def deserialize(self, stream):
        self.length.deserialize(stream)
        items = []
        for i in xrange(self.length.get_value()):
            subfield = self.field_class()
            subfield.deserialize(stream)
            items.append(subfield)

        self.value = items

    def serialize(self, stream):
        self.length.serialize(stream)
        for field in self.value:
            field.serialize(stream)

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

class IPv4AddressField(Field):
    """An IPv4 address field without timestamp and reserved IPv6 space."""
    reserved = "\x00"*10 + "\xff"*2

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def deserialize(self, stream):
        unused_reserved = stream.read(12)
        addr = stream.read(4)
        self.value = socket.inet_ntoa(addr)

    def serialize(self, stream):
        stream.write(self.reserved)
        stream.write(socket.inet_aton(self.value))

class VariableIntegerField(Field):
    """A variable size integer field."""
    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def deserialize(self, stream):
        int_id_raw = stream.read(struct.calcsize("<B"))
        int_id = struct.unpack("<B", int_id_raw)[0]
        if int_id == 0xFD:
            int_id = struct.unpack("<H", stream.read(2))[0]
        elif int_id == 0xFE:
            int_id = struct.unpack("<I", stream.read(4))[0]
        elif int_id == 0xFF:
            int_id = struct.unpack("<Q", stream.read(8))[0]
        self.value = int(int_id)

    def serialize(self, stream):
        if self.value < 0xFD:
            data = chr(self.value)
        if self.value <= 0xFFFF:
            data = chr(0xFD) + struct.pack("<H", self.value)
        if self.value <= 0xFFFFFFFF:
            data = chr(0xFE) + struct.pack("<I", self.value)
        data = chr(0xFF) + struct.pack("<Q", self.value)
        stream.write(data)

class VariableStringField(Field):
    """A variable length string field."""
    length = VariableIntegerField()

    def set_value(self, value):
        self.length.set_value(len(value))
        self.value = value

    def get_value(self):
        return self.value

    def deserialize(self, stream):
        self.length.deserialize(stream)
        string_value = stream.read(self.length.get_value())
        self.value = str(string_value)

    def serialize(self, stream):
        self.length.serialize(stream)
        stream.write(self.value)

    def __len__(self):
        return len(self.value)

class Hash(Field):
    """A hash type field."""
    datatype = "<I"

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def deserialize(self, stream):
        data_size = struct.calcsize(self.datatype)
        intvalue = 0
        for i in range(8):
            data = stream.read(data_size)
            val = struct.unpack(self.datatype, data)[0]
            intvalue += val << (i * 32)
        self.value = intvalue

    def serialize(self, stream):
        hash_ = self.value
        for i in range(8):
            stream.write(struct.pack(self.datatype, hash_ & 0xFFFFFFFF))
            hash_ >>= 32
