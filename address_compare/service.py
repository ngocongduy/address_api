# from elasticsearch_dsl.connections import connections

from .documents import AddressDocument
from .search_engine.helps import SearchHelper
from .search_engine.utils import clean_and_split_into_parts_for_formatted_address, clean_and_split_into_words_sorted
from .address_comparison.address_comparison import AddressComparer

from django.conf import settings

geocoding_api_key = getattr(settings, "GOOGLE_API_KEY", '')
import requests
from geopy import distance


class DecisionEngine:
    def __init__(self, addresses, index_name):
        # connections.create_connection(hosts=['localhost:9200'])
        AddressDocument.init()
        self.comparer = AddressComparer()
        self.addresses = addresses
        self.index_name = index_name

    def __check_in_elasticsearch(self, query_term: str, index_name: str):
        result = []
        print(query_term)
        cleaned_address = self.__make_cleaned_address(query_term)
        print(cleaned_address)
        if cleaned_address is not None:
            searcher = SearchHelper(index_name)
            query = {
                "bool": {
                    "must": {
                        "match": {
                            "cleaned_address": {
                                "query": cleaned_address,
                                "analyzer": "keyword"
                            }
                        }
                    }
                }
            }
            try:
                result = searcher.query(query_body=query, size=1)
            except Exception as e:
                print(e)

        return result

    def __extract_address(self, address):
        # if type(address) is dict:
        #     ele = [e for e in address.values() if e]
        #     print(ele)
        #     rebuilt_address = ','.join(ele)
        #     extracted_address = self.comparer.extractor.assumption_brute_force_search_word_dict(address=rebuilt_address,
        #                                                                                         key_value_pairs=address)
        #     print("Rebuilt address" + rebuilt_address)
        # else:
        #     extracted_address = self.comparer.extractor.assumption_brute_force_search_word_dict(address=address)
        extracted_address = self.comparer.extractor.assumption_brute_force_search_word_dict(address=address)
        if extracted_address is not None:
            return ', '.join([extracted_address.get(e) for e in ('street', 'ward', 'district', 'province') if
                              extracted_address.get(e) is not None])
        else:
            return ''

    def __compare_address(self, address1, address2):
        return self.comparer.brute_compare(address1, address2)


    def __make_cleaned_address(self, address):
        cleaned_address = clean_and_split_into_words_sorted(address)
        if len(cleaned_address) > 0:
            return ' '.join(cleaned_address)
        else:
            return None


    def __check_and_call(self, addresses, index_name):
        coordinates = []
        returned_addresses = []
        for address in addresses:

            check_result = self.__check_in_elasticsearch(address, index_name)
            # print(check_result)
            if len(check_result) > 0:
                values = check_result[0].get('_source')
                return_extracted_address = ''
                if values is not None:
                    coordinates.append((values.get('lat', 0), values.get('long', 0)))
                    return_extracted_address = values.get('extracted_original_address','error')
                else:
                    coordinates.append((0, 0))
                returned_addresses.append(return_extracted_address)

            else:
                response_from_google = self.__call_google_geocoding(address)
                formatted_long_lat = self.__get_formatted_long_lat(response_from_google)
                formatted_address = ''
                long = 0
                lat = 0
                original_address = address
                cleaned_address = self.__make_cleaned_address(address)
                extracted_original_address = ''
                extracted_formatted_address = ''
                if formatted_long_lat is not None:
                    formatted_address = formatted_long_lat[2]
                    long = formatted_long_lat[1]
                    lat = formatted_long_lat[0]
                    # print(formatted_long_lat)
                if len(formatted_address) > 0:
                    cleaned_formatted_address = clean_and_split_into_parts_for_formatted_address(formatted_address)
                    # print("Cleaned formatted address")
                    # print(cleaned_formatted_address)
                    extracted_formatted_address = self.__extract_address(cleaned_formatted_address)
                if len(original_address) > 0:
                    extracted_original_address = self.__extract_address(original_address)
                # AddressDocument.init()
                doc = AddressDocument(
                    cleaned_address=cleaned_address,
                    original_address=original_address,
                    formatted_address=formatted_address,
                    extracted_original_address=extracted_original_address,
                    extracted_formatted_address=extracted_formatted_address,
                    long=long,
                    lat=lat
                )
                # save with index refreshed to make sure new inserted data alive for the next iterate
                doc.save(refresh=True)
                coordinates.append((lat, long))
                returned_addresses.append(extracted_original_address)
        return coordinates, returned_addresses


    def __compute_distance(self, coordinate1, coordinate2):
        for coor in [coordinate1,coordinate2]:
            if coor == (0, 0):
                cd = -1
                return cd
        cd = distance.great_circle(coordinate1, coordinate2).km
        return cd


    def __call_google_geocoding(self, address):
        base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {'address': address, 'key': geocoding_api_key}
        res = requests.get(base_url, params)
        print(res.json())
        return res.json()

    def __get_formatted_long_lat(self, response_from_google: dict):
        result = response_from_google.get('results', '')
        if len(result) > 0:
            true_result = result[0]
            geometry = true_result.get('geometry')
            location = geometry.get('location')
            long = location.get('lng')
            lat = location.get('lat')

            formatted_address = true_result.get('formatted_address', '')

            return lat, long, formatted_address
        else:
            return None

    def make_decision(self):
        result_from_check_and_call = self.__check_and_call(self.addresses, self.index_name)
        coordinates = result_from_check_and_call[0]
        original_extracted_addresses = result_from_check_and_call[1]
        result= {'distance':'inf','matched':False, "matched_rate":0,"mapped_original_address1":"","mapped_original_address2":""}
        print(coordinates)
        print(original_extracted_addresses)
        if len(coordinates) == 2 and len(original_extracted_addresses) == 2:
            cd = self.__compute_distance(*coordinates)
            compare_result = self.__compare_address(*original_extracted_addresses)
            print(compare_result)
            # Evaluate result with biased
            rate = 0
            biased = {'street':0.1,'ward':0.2,'district':0.3,'province':0.4}
            for k, b in biased.items():
                rate += compare_result.get(k,0) * b
            print(rate)
            if cd >= 0 and rate>= 80:
                result['distance'] = cd
                result['matched'] = True
                result['matched'] = rate
                result['mapped_original_address1'] = original_extracted_addresses[0]
                result['mapped_original_address2'] = original_extracted_addresses[1]

            else:
                result['matched'] = rate
                result['mapped_original_address1'] = original_extracted_addresses[0]
                result['mapped_original_address2'] = original_extracted_addresses[1]
            return result
        else:
            return None




