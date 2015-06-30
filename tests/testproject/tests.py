from django.test import TestCase

from .models import TestResource, RelatedResource1, RelatedResource2


class NestedFieldsTest(TestCase):
    def setUp(self):
        self.related_resource_1 = RelatedResource1.objects.create(name="Related-Resource1")
        self.nested_related_resource_1_1 = RelatedResource1.objects.create(name="Nested-Related-Resource11")
        self.nested_related_resource_1_2 = RelatedResource1.objects.create(name="Nested-Related-Resource12")
        self.related_resource_2 = RelatedResource2.objects.create(name="Related-Resource2")
        self.related_resource_2.related_resources_1.add(self.nested_related_resource_1_1, self.nested_related_resource_1_2)
        self.test_resource_1 = TestResource.objects.create(name="Test-Resource", related_resource_1=self.related_resource_1,
                                                           related_resource_2=self.related_resource_2)

    def testGetNestedFieldsStatic(self):
        resp = self.client.get("/test-resources/")
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(1, len(resp.data))
        test_resource_data = resp.data[0]
        self.assertEqual(4, len(test_resource_data))
        self.assertEqual(self.test_resource_1.id, test_resource_data['id'])
        self.assertEqual(self.test_resource_1.name, test_resource_data['name'])
        self.assertEqual(self.test_resource_1.related_resource_1.id, test_resource_data['related_resource_1'])
        related_resource_2_data = test_resource_data['related_resource_2']
        self.assertEqual(2, len(related_resource_2_data))
        self.assertEqual(self.related_resource_2.name, related_resource_2_data['name'])
        nested_related_resources_data = related_resource_2_data['related_resources_1']
        self.assertEqual(2, len(nested_related_resources_data))
        self.assertEqual(self.nested_related_resource_1_1.id, nested_related_resources_data[0]['id'])
        self.assertEqual(self.nested_related_resource_1_1.name, nested_related_resources_data[0]['name'])
        self.assertEqual(self.nested_related_resource_1_2.id, nested_related_resources_data[1]['id'])
        self.assertEqual(self.nested_related_resource_1_2.name, nested_related_resources_data[1]['name'])

    def testGetNestedFieldsDynamic(self):
        resp = self.client.get("/test-resources/?fields=related_resource_1.fields(active),related_resource_2.fields("
                               "related_resources_1.fields(active))")
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(1, len(resp.data))
        test_resource_data = resp.data[0]
        self.assertEqual(3, len(test_resource_data))
        self.assertEqual(self.test_resource_1.id, test_resource_data['id'])
        related_resource_1_data = test_resource_data['related_resource_1']
        self.assertEqual(2, len(related_resource_1_data))
        self.assertEqual(self.test_resource_1.related_resource_1.id, related_resource_1_data['id'])
        self.assertEqual(self.test_resource_1.related_resource_1.active, related_resource_1_data['active'])
        related_resource_2_data = test_resource_data['related_resource_2']
        self.assertEqual(2, len(related_resource_2_data))
        self.assertEqual(self.related_resource_2.id, related_resource_2_data['id'])
        nested_related_resources_data = related_resource_2_data['related_resources_1']
        self.assertEqual(2, len(nested_related_resources_data))
        self.assertEqual(self.nested_related_resource_1_1.id, nested_related_resources_data[0]['id'])
        self.assertEqual(self.nested_related_resource_1_1.active, nested_related_resources_data[0]['active'])
        self.assertEqual(self.nested_related_resource_1_2.id, nested_related_resources_data[1]['id'])
        self.assertEqual(self.nested_related_resource_1_2.active, nested_related_resources_data[1]['active'])
