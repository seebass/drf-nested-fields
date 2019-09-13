from rest_framework.fields import empty
from rest_framework.utils.field_mapping import get_nested_relation_kwargs


class NestedFieldsSerializerMixin(object):
    """
    Serializer for serializing defined nested fields of django models
    Addional Meta field `nested_fields` to explicitly define serialized fields with following structure
    {"field1": (["field11"], {"nested_field12": (["field121"], {})})}
    """
    nested_serializer_class = None

    def __init__(self, instance=None, data=empty, **kwargs):
        super(NestedFieldsSerializerMixin, self).__init__(instance, data, **kwargs)
        if not self.nested_serializer_class:
            self.nested_serializer_class = self.__class__
        self.__add_nested_fields_to_fields()

    def build_field(self, field_name, info, model_class, nested_depth):
        if hasattr(self.Meta, "nested_fields") and field_name in self.Meta.nested_fields:
            nested_depth = 1
        return super(NestedFieldsSerializerMixin, self).build_field(field_name, info, model_class, nested_depth)

    def build_nested_field(self, field_name, relation_info, nested_depth):
        class NestedSerializer(self.nested_serializer_class):
            class Meta:
                model = relation_info.related_model
                depth = nested_depth - 1

        if field_name in self.Meta.nested_fields:
            fields, nested_fields = self.Meta.nested_fields[field_name]
            NestedSerializer.Meta.fields = fields
            NestedSerializer.Meta.nested_fields = nested_fields

        field_class = NestedSerializer
        field_kwargs = get_nested_relation_kwargs(relation_info)

        return field_class, field_kwargs

    def __add_nested_fields_to_fields(self):
        if not hasattr(self.Meta, "fields") or not hasattr(self.Meta, "nested_fields"):
            return

        self.Meta.fields = list(self.Meta.fields)
        for field_name in self.Meta.nested_fields:
            if field_name not in self.Meta.fields:
                self.Meta.fields.append(field_name)
