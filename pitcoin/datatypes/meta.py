from django.db import models

class Field(object):
    """Messages and structures are defined using Fields, which define the field name,
    serializer type, and default value."""
    def __init__(self, name, serializer, default=None):
        self.name = name
        self.serializer = serializer
        self.default = default

class BitcoinSerializable(object):
    def __init__(self, *args, **kwargs):
        """Deserialize the model from the given stream, or instantiate with the given arguments"""

        # If a stream was specified, remove it from kwargs
        stream = kwargs.get('stream')
        if 'stream' in kwargs:
            del kwargs['stream']

        # Run the model init if this is a db model subclass
        if issubclass(self.__class__, models.Model):
            super().__init__(*args, **kwargs)

        if stream is not None:
            self.deserialize(stream)
        else:
            # Set the default, or specified keyword arguments - but not if the attribute already exists
            # (They can exist if the derived class also is a django-orm model, which was currently queried
            # from the DB)
            for field in self._fields:
                if hasattr(self, field.name):
                    continue
                if field.name in kwargs:
                    setattr(self, field.name, kwargs[field.name])
                else:
                    # The default can be a callable, if so, call it
                    if not callable(field.default):
                        setattr(self, field.name, field.default)
                    else:
                        setattr(self, field.name, field.default())

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
