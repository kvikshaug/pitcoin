class Field(object):
    """Messages and structures are defined using Fields, which define the field name,
    serializer type, and default value."""
    def __init__(self, name, serializer, default=None):
        self.name = name
        self.serializer = serializer
        self.default = default

class BitcoinSerializable(object):
    def __init__(self, stream=None, *args, **kwargs):
        """Deserialize the model from the given stream, or instantiate with the given arguments"""
        if stream is not None:
            self.deserialize(stream)
        else:
            # Set the default values
            for field in self._fields:
                if not callable(field.default):
                    setattr(self, field.name, field.default)
                else:
                    setattr(self, field.name, field.default())

            # Now override with the given arguments
            for field, value in list(kwargs.items()):
                setattr(self, field, value)

    def deserialize(self, stream):
        """Deserialize this model from the given stream"""
        for field in self._fields:
            setattr(self, field.name, field.serializer.deserialize(stream))
        return self

    def serialize(self, stream, value=None):
        """Serialize the current data in this model to the given stream. Note that we're
        ignoring the value paramenter which is used by nested fields, but not needed since
        this is a model structure and not a field."""
        for field in self._fields:
            field.serializer.serialize(stream, getattr(self, field.name))
