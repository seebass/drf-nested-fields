from rest_framework.viewsets import ModelViewSet
from drf_nested_fields.views import CustomFieldsMixin

from .models import TestResource
from .serializers import TestResourceSerializer


class TestResourceViewSet(CustomFieldsMixin, ModelViewSet):
    serializer_class = TestResourceSerializer
    queryset = TestResource.objects.all()
