import re

from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor
)

from drf_nested_fields.serializers import NestedFieldsSerializerMixin


def copy_meta_attributes(source_meta, target_meta):
    for attr_key in source_meta.__dict__.keys():
        if attr_key.startswith("_") or hasattr(target_meta, attr_key):
            continue
        attr_value = source_meta.__dict__[attr_key]
        setattr(target_meta, attr_key, attr_value)


class CustomFieldsMixin(object):
    always_included_fields = ["id"]

    _GET_FIELDS_PATTERN = re.compile(r"([a-zA-Z0-9_-]+?)\.fields\((.*?)\)\Z")

    def get_serializer_class(self):
        serializer_class = super(CustomFieldsMixin, self).get_serializer_class()

        custom_field_serializer_class = self._get_custom_field_serializer_class(serializer_class)
        if custom_field_serializer_class:
            return custom_field_serializer_class

        return serializer_class

    def get_queryset(self):
        """
        For reducing the query count the queryset is expanded with `prefetch_related` and `select_related` depending on the
        specified fields and nested fields
        """
        self.queryset = super(CustomFieldsMixin, self).get_queryset()
        serializer_class = self.get_serializer_class()
        if hasattr(serializer_class.Meta, 'nested_fields'):
            nested_fields = serializer_class.Meta.nested_fields
            fields = serializer_class.Meta.fields
            self._expand_queryset(fields, nested_fields, self.queryset.model)
        return self.queryset

    def _get_custom_field_serializer_class(self, base_serializer_class):
        if not issubclass(base_serializer_class, NestedFieldsSerializerMixin):
            return None

        request = self.get_serializer_context().get('request')
        if not request or 'fields' not in request.query_params:
            return None

        custom_fields_str = request.query_params['fields']
        custom_fields, custom_nested_fields = self._get_custom_fields(custom_fields_str)

        class CustomFieldSerializer(base_serializer_class):
            class Meta:
                fields = custom_fields
                nested_fields = custom_nested_fields
                exclude = None

            copy_meta_attributes(base_serializer_class.Meta, Meta)

        return CustomFieldSerializer

    def _get_custom_fields(self, custom_fields_str):
        custom_nested_fields = dict()
        custom_fields = []
        splitted_custom_field_strs = self.__split_custom_fields(custom_fields_str)
        for custom_field_str in splitted_custom_field_strs:
            sub_fields_match = self._GET_FIELDS_PATTERN.search(custom_field_str)
            if sub_fields_match:
                field_name = sub_fields_match.group(1)
                custom_nested_fields[field_name] = self._get_custom_fields(sub_fields_match.group(2))
            else:
                custom_fields.append(custom_field_str)
        return self.always_included_fields + custom_fields, custom_nested_fields

    @staticmethod
    def __split_custom_fields(custom_fieldsStr):
        parenthesis_ounter = 0
        splitted_custom_field_strs = []
        found_custom_field = ""

        for char in custom_fieldsStr:
            if char == "(":
                parenthesis_ounter += 1
            if char == ")":
                parenthesis_ounter -= 1
            if char == "," and parenthesis_ounter == 0:
                splitted_custom_field_strs.append(found_custom_field)
                found_custom_field = ""
                continue
            found_custom_field += char
        splitted_custom_field_strs.append(found_custom_field)
        return splitted_custom_field_strs

    def _expand_queryset(self, fields, nested_fields, model, prefix='', parent_prefetched=False):
        for field_name in (f for f in fields if f not in nested_fields):
            field = getattr(model, field_name, None)
            if not field:
                continue
            if isinstance(field, (ForwardManyToOneDescriptor, ReverseOneToOneDescriptor)):
                self._add_single_related_field_to_query(prefix, field_name, parent_prefetched)
            elif isinstance(field, (ReverseManyToOneDescriptor, ManyToManyDescriptor)):
                self._add_many_related_field_to_query(prefix, field_name)
        for field_name in nested_fields:
            field = getattr(model, field_name, None)
            if not field:
                continue
            related_model = None
            if isinstance(field, ReverseOneToOneDescriptor):
                related_model = field.related.related_model
                self._add_single_related_field_to_query(prefix, field_name, parent_prefetched)
            elif isinstance(field, ForwardManyToOneDescriptor):
                related_model = field.field.related_model
                self._add_single_related_field_to_query(prefix, field_name, parent_prefetched)
            elif isinstance(field, ReverseManyToOneDescriptor):
                related_model = field.rel.related_model
                self._add_many_related_field_to_query(prefix, field_name)
                parent_prefetched = True
            elif isinstance(field, ManyToManyDescriptor):
                related_model = field.field.related_model
                self._add_many_related_field_to_query(prefix, field_name)
                parent_prefetched = True

            if related_model:
                self._expand_queryset(nested_fields[field_name][0], nested_fields[field_name][1], related_model,
                                      prefix + field_name + '__', parent_prefetched)

    def _add_single_related_field_to_query(self, prefix, field_name, parent_prefetched):
        if parent_prefetched:
            self.queryset = self.queryset.prefetch_related(prefix + field_name)
        else:
            self.queryset = self.queryset.select_related(prefix + field_name)

    def _add_many_related_field_to_query(self, prefix, field_name):
        self.queryset = self.queryset.prefetch_related(prefix + field_name)
