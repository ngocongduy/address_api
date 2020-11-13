from rest_framework import status

from address_compare.serializers import AddressRequestSerializer

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .address_comparison import address_comparison

comparer = address_comparison.AddressComparer()

@api_view(['GET'])
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@api_view(['POST'])
def post_address_compare(request):
    if request.method == 'POST':
        data = {'address_source': request.data.get('address_source'), 'address_compare': request.data.get('address_compare')}
        serializer = AddressRequestSerializer(data=data)
        if serializer.is_valid():
            # serializer.save()
            addr_1 = serializer.data.get('address_source')
            addr_2 = serializer.data.get('address_compare')
            compare_result = comparer.fuzzy_compare(addr_1, addr_2)

            return Response(compare_result, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
