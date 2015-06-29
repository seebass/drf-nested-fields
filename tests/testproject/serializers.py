from rest_framework.serializers import ModelSerializer
from drf_nested_fields.serializers import NestedFieldsSerializerMixin
from .models import TestResource


class TestResourceSerializer(NestedFieldsSerializerMixin, ModelSerializer):
    class Meta:
        model = TestResource
        fields = ('id', 'name', 'related_resource_1')
        nested_fields = {
            'related_resource_2': (
                ['name'],
                {
                    'related_resources_1': (
                        ['id', 'name'],
                        {}
                    )
                })
        }
