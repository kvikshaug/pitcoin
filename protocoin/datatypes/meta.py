import copy

import fields

class DataModel(object):

    _fields = {}

    def __init__(self, stream=None, *args, **kwargs):
        """Create this data model, deserialized from the stream or from the provided arguments"""

        # Copy datamodel class fields to an internal field dict on the instance
        object.__setattr__(self, '_fields', {})
        for field_name, field in self.__class__.__dict__.items():
            if isinstance(field, fields.Field) or isinstance(field, DataModel):
                self._fields[field_name] = copy.deepcopy(field)

            # If this is a field, set the new default value which may or may not differ
            if isinstance(field, fields.Field):
                field.set_value(field.get_default())

        # Set the field order, which is used when serializing
        self.order = fields.Field.order
        fields.Field.order += 1

        # Deserialize the model from the given stream, or instantiate with the given fields
        if stream is not None:
            self.deserialize(stream)
        else:
            for field, value in kwargs.items():
                setattr(self, field, value)

    def __getattribute__(self, name):
        """Get the field value if datamodel field"""
        if name in object.__getattribute__(self, '_fields'):
            return object.__getattribute__(self, '_fields')[name].get_value()
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        """Set the field value if datamodel field"""
        if name in object.__getattribute__(self, '_fields'):
            object.__getattribute__(self, '_fields')[name].set_value(value)
        else:
            object.__setattr__(self, name, value)

    def deserialize(self, stream):
        """Deserialize this model from the given stream"""
        for field in [field for field in sorted(self._fields.values(), key=lambda f: f.order)]:
            field.deserialize(stream)

    def serialize(self, stream):
        """Serialize the current data in this model to the given stream"""
        for field in [field for field in sorted(self._fields.values(), key=lambda f: f.order)]:
            field.serialize(stream)

    def get_value(self):
        """Called in nested structures. Return the child data structure"""
        return self
