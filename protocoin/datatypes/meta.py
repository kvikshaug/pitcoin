import fields

class DataModel(object):
    def __init__(self, stream=None, *args, **kwargs):
        """Create this data model, deserialized from the stream or from the provided arguments"""
        # Set the field order, which is used when serializing
        self.order = fields.Field.order
        fields.Field.order += 1

        if stream is not None:
            self.deserialize(stream)
        else:
            for field, value in kwargs.items():
                self.__setattr__(field, value)

    def __getattribute__(self, name):
        """Get a field value, or fallback to the normal attribute if not a datamodel field"""
        attribute = object.__getattribute__(self, name)
        if object.__getattribute__(self, '_is_managed_field')(attribute):
            return self._get_field_instance(name).get_value()
        else:
            return attribute

    def __setattr__(self, name, value):
        """Set a field value, or a normal attribute if not a datamodel field"""
        if hasattr(self, name) and self._is_managed_field(object.__getattribute__(self, name)):
            self._get_field_instance(name).set_value(value)
        else:
            object.__setattr__(self, name, value)

    def _get_field_instance(self, name):
        """Return the real field instance instead of its value"""
        return object.__getattribute__(self, name)

    def _is_managed_field(self, field):
        return isinstance(field, fields.Field) or isinstance(field, DataModel)

    _managed_fields_cache = None
    def _managed_field_names(self):
        """Return the attribute names that we're managing as data fields"""
        if self._managed_fields_cache is None:
            self._managed_fields_cache = [f for f in dir(self) if self._is_managed_field(object.__getattribute__(self, f))]
        return self._managed_fields_cache

    def deserialize(self, stream):
        """Deserialize this model from the given stream"""
        fields = [self._get_field_instance(field) for field in self._managed_field_names()]
        for field in sorted(fields, key=lambda f: f.order):
            field.deserialize(stream)

    def serialize(self, stream):
        """Serialize the current data in this model to the given stream"""
        fields = [self._get_field_instance(field) for field in self._managed_field_names()]
        for field in sorted(fields, key=lambda f: f.order):
            field.serialize(stream)

    def get_value(self):
        """Called in nested structures. Return the child data structure"""
        return self
