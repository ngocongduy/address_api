from rest_framework import status
import elasticsearch
from address_compare.serializers import AddressRequestSerializer

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .address_comparison import address_comparison

# import the logging library
import logging
import requests
import asyncio
import aiohttp
from geopy import distance

# Elastic search
from .documents import AddressDocument
from .search_engine.helps import AddressElasticSearchService, SearchHelper
from .search_engine.utils import is_not_empty_or_null

from django.conf import settings

from .service import DecisionEngine

geocoding_api_key = getattr(settings, "GOOGLE_API_KEY", '')

# Get an instance of a logger
# logger = logging.getLogger(__name__)
logger = logging.getLogger('django')
logging.basicConfig(level=logging.INFO)

comparer = address_comparison.AddressComparer()


def remove_some_value(compare_result):
    key_to_remove = {'count','type','addr1_pos','addr2_pos'}
    if type(compare_result) is dict:
        for k in key_to_remove:
            try:
                compare_result.pop(k)
            except:
                pass
    return compare_result

@api_view(['GET'])
def index(request):
    return HttpResponse("Hello, world!")

# Naive compare
@api_view(['POST'])
def post_address_compare(request):
    data = {'address_source': request.data.get('address_source'),
            'address_compare': request.data.get('address_compare')}
    serializer = AddressRequestSerializer(data=data)
    if serializer.is_valid():
        # serializer.save()
        addr_1 = serializer.data.get('address_source')
        addr_2 = serializer.data.get('address_compare')
        compare_result = comparer.fuzzy_compare(addr_1, addr_2)
        msg = str(compare_result)
        print(msg)
        # logger.debug("Data: ".format(msg))
        compare_result = remove_some_value(compare_result)
        return Response(compare_result, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def post_address_compare_list(request):
    if request.method == 'POST':
        # print(request.data)
        data = {'address_source': request.data.get('address_source'),
                'address_compare_list': request.data.get('address_compare_list')}
        if data.get('address_compare_list') is not None:
            data_list = [{'address_source': data.get('address_source'), 'address_compare': e} for e in
                         data.get('address_compare_list')]
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
                    compare_result = remove_some_value(compare_result)
                    result_list.append(compare_result)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(result_list, status=status.HTTP_200_OK)


async def async_call_google_geocoding(session, base_url, params):
    async with session.get(base_url, params=params) as resp:
        # print(resp)
        data = await resp.json()
        data['address'] = params.get('address')
        return data


async def async_call_all_google_geocoding(addresses):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    tasks = []
    async with aiohttp.ClientSession() as session:
        for address in addresses:
            # print(address)
            if type(address) is str:
                params = {'address': address, 'key': geocoding_api_key}
                tasks.append(async_call_google_geocoding(session, base_url, params))
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses


def get_long_lat(response_from_google: dict):
    result = response_from_google.get('results', '')
    if len(result) > 0:
        true_result = result[0]
        geometry = true_result.get('geometry')
        location = geometry.get('location')
        long = location.get('lng')
        lat = location.get('lat')
        return lat, long
    else:
        return None

# Check calling google api with simple async method
@api_view(['POST'])
def async_post_address_locate(request):
    if request.method == 'POST':
        address = request.data.get('address')
        if type(address) is str:
            print(address)
            addresses = [address]
            extracted_result = comparer.extractor.assumption_brute_force_search_word_dict(address)
            if extracted_result is not None:
                ward = extracted_result.get('ward')
                district = extracted_result.get('district')
                province = extracted_result.get('province')
                new_address = ', '.join([ward, district, province])
                print(new_address)
                addresses.append(new_address)
            responses = asyncio.run(async_call_all_google_geocoding(addresses))
            # print(responses)
            coordinates = []
            # print(responses)
            for response_from_google in responses:
                # print(response_from_google)
                coordinate = get_long_lat(response_from_google)
                if coordinate is not None:
                    coordinates.append(coordinate)
            cd = 'unable to get distance, one component may be unlocated!'
            # print(coordinates)
            if len(coordinates) == 2:
                cd = distance.great_circle(coordinates[0], coordinates[1]).km
            final_result = {'great_circle_distance_km': cd, 'google_geocoding': responses}
            return Response(final_result, status=status.HTTP_200_OK)
    return Response({"error": "address should be a string"}, status=status.HTTP_400_BAD_REQUEST)


# For Elastic search
@api_view(['POST'])
def save_data_elastic_search(request):
    address = request.data.get('address')
    print(address)
    content = {
        "message": "",
        "result": ""
    }
    if not is_not_empty_or_null(address):
        content["message"] = "Address should be a string and not empty"
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    else:
        original_address = address
        formatted_address = address
        AddressDocument.init()
        addressComponent = AddressDocument(
            cleaned_address=original_address,
            original_address=original_address,
            formatted_address=formatted_address,
            extracted_original_address=original_address,
            extracted_formatted_address=formatted_address,
            long=0,
            lat=0
        )
        is_success = True
        try:
            addressComponent.save()
        except Exception as e:
            print(e)
            is_success = False
        if is_success:
            content['message'] = "Created"
            content['result'] = str(addressComponent)
            return Response(content, status=status.HTTP_201_CREATED)
        else:
            content['message'] = 'Failed'
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_address(request):
    def _send_response(message, status_code, data=None):
        content = {
            "message": message,
            "result": data if data is not None else []
        }
        return Response(content, status=status_code)

    query = request.data.get('queries', None)
    k = request.data.get('k', None)
    print(request.data)

    if not is_not_empty_or_null(query):
        error_message = "queries should not be empty"
        return _send_response(error_message, status.HTTP_400_BAD_REQUEST)

    if not is_not_empty_or_null(k):
        error_message = "k should be integer and not empty"
        return _send_response(error_message, status.HTTP_400_BAD_REQUEST)

    try:
        index_name = "addresses"
        searcher = SearchHelper(index_name)
        if type(query) is dict:
            query_body = query
        else:
            query_body ={
                "bool": {
                    "must": {
                        "match": {
                            "original_address": {
                                "query": query,
                                "analyzer": "fingerprint"
                            }
                        }
                    }
                }
            }

        result = searcher.query(query_body=query_body, size=k)
        response = result

    except elasticsearch.ConnectionError as connection_error:
        # ConnectionError if elasticsearch server is down
        logger.debug('ConnectionError: ' + str(connection_error))
        error_message = "Elastic search Connection refused"
        return _send_response(error_message, status.HTTP_503_SERVICE_UNAVAILABLE)

    except Exception as exception_msg:
        # handle all type of error
        logger.debug('Exception: ' + str(exception_msg))
        error_message = str(exception_msg)
        return _send_response(error_message, status.HTTP_400_BAD_REQUEST)

    return _send_response('success', status.HTTP_200_OK, response)


@api_view(['POST'])
def compare_addresses(request):
    def _send_response(message, status_code, data=None):
        content = {
            "message": message,
            "result": data if data is not None else []
        }
        return Response(content, status=status_code)

    address1 = request.data.get('address1')
    address2 = request.data.get('address2')

    if not is_not_empty_or_null(address1):
        error_message = "please provide address 1"
        return _send_response(error_message, status.HTTP_400_BAD_REQUEST)

    if not is_not_empty_or_null(address2):
        error_message = "please provide address 2"
        return _send_response(error_message, status.HTTP_400_BAD_REQUEST)

    try:
        index_name = "addresses"

        decisionMaker = DecisionEngine([address1, address2], index_name)
        result = decisionMaker.make_decision()
        print(result)
        if result is not None:
            result["original_address1"] = address1
            result["original_address2"] = address2
        response = result

    except elasticsearch.ConnectionError as connection_error:
        # ConnectionError if elasticsearch server is down
        logger.debug('ConnectionError: ' + str(connection_error))
        error_message = "Elastic search Connection refused"
        return _send_response(error_message, status.HTTP_503_SERVICE_UNAVAILABLE)

    except Exception as exception_msg:
        # handle all type of error
        logger.debug('Exception: ' + str(exception_msg))
        error_message = str(exception_msg)
        return _send_response(error_message, status.HTTP_400_BAD_REQUEST)

    return _send_response('success', status.HTTP_200_OK, response)
