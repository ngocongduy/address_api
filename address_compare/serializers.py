from rest_framework import serializers

from address_compare.models import AddressRequest


class AddressRequestSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AddressRequest
        fields = ['address_source','address_compare']
