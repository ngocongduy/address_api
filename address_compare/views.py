from rest_framework import status

from address_compare.serializers import AddressRequestSerializer

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .address_comparison import address_comparison

# import the logging library
import logging

# Get an instance of a logger
# logger = logging.getLogger(__name__)
logger = logging.getLogger('django')
logging.basicConfig(level=logging.INFO)

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
            msg = str(compare_result)
            print(msg)
            # logger.debug("Data: ".format(msg))
            return Response(compare_result, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def post_address_compare_list(request):
    if request.method == 'POST':
        # print(request.data)
        data = {'address_source': request.data.get('address_source'), 'address_compare_list': request.data.get('address_compare_list')}
        if data.get('address_compare_list') is not None:
            data_list = [{'address_source': data.get('address_source'),'address_compare': e} for e in data.get('address_compare_list')]
            print(data_list)
            result_list = []
            for pair in data_list:
                print(pair)
                serializer = AddressRequestSerializer(data=pair)
                if serializer.is_valid():
                    addr_1 = serializer.data.get('address_source')
                    addr_2 = serializer.data.get('address_compare')
                    print(addr_1)
                    print(addr_2)

                    compare_result = comparer.fuzzy_compare(addr_1, addr_2)
                    logger.info(compare_result)
                    result_list.append(compare_result)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(result_list, status=status.HTTP_200_OK)