drf-nested-fields
=================
Extension for Django REST Framework 3 which allows for defining custom field serialization.

## Setup ##

	pip install drf-nested-fields

## Requirement ##

* Python 2.7+
* Django 1.6+
* Django REST Framework 3

## Features ##
In addition to the standard Django REST Framework Meta attribute *depth*, this framework provides the possibility to explicitly define which fields should be serialized. This can be achieved for the following model in two ways:

	class RelatedResource1(models.Model):
    	name = models.CharField(max_length=255)
    	active = models.BooleanField(default=True)

	class RelatedResource2(models.Model):
    	name = models.CharField(max_length=255)
    	active = models.BooleanField(default=True)
    	related_resources_1 = models.ManyToManyField(RelatedResource1)

	class TestResource(models.Model):
    	related_resource_1 = models.ForeignKey(RelatedResource1)
    	related_resource_2 = models.OneToOneField(RelatedResource2)
    	name = models.CharField(max_length=255)
		
	

1. Use **NestedFieldsSerializerMixin** and set the Meta attribute **nested_fields** on the serializer.
		
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
                		}
                	)
        		}
	Result:
		
		[
			"id": 1,
			"name": "Test-Resource",
			"related_resource_1": 5,
			"related_resource_2": {
				"name": "Related-Resource-2",
				"related_resources_1": [
					{
						"id": 234,
						"name": "Nested-Related-Resource11",
					},
					{
						"id": 235,
						"name": "Nested-Related-Resource12",
					}
				]
			}
		]
2. Use **CustomFieldsMixin** in your view and set query parameter **fields**. The **id** is returned because of the attribute **always_included_fields** which can be overridden in your custom view.
	
		class TestResourceViewSet(CustomFieldsMixin, ModelViewSet):
    		serializer_class = TestResourceSerializer
    		queryset = TestResource.objects.all()
    		
    	GET http://testserver/test-resources/?fields=related_resource_2.fields("
                               "related_resources_1.fields(active))
                      
	Result:
		
		[
			"id": 1,
			"related_resource_2": {
				"name": "Related-Resource-2",
				"related_resources_1": [
					{
						"id": 234,
						"active": true,
					},
					{
						"id": 235,
						"active": false,
					}
				]
			}
		]         