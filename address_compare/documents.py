from django_elasticsearch_dsl import Document, Text, Date, Double
# from django_elasticsearch_dsl.registries import registry
from datetime import datetime
# from .models import AddressComponent

# @registry.register_document
# class AddressDocument(Document):
#     class Index:
#         # Name of the Elasticsearch index
#         name = 'addresses'
#         # See Elasticsearch Indices API reference for available settings
#         settings = {'number_of_shards': 1,
#                     'number_of_replicas': 0,
#                     # "analysis": {
#                     #     "analyzer": {
#                     #         "default": {
#                     #             "type": "fingerprint"
#                     #         },
#                     #         "default_search": {
#                     #             "type": "fingerprint"
#                     #         }
#                     #     }
#                     # }
#                     }
#
#         # {
#         #     "settings": {
#         #         "analysis": {
#         #             "analyzer": {
#         #                 "default": {
#         #                     "type": "simple"
#         #                 },
#         #                 "default_search": {
#         #                     "type": "whitespace"
#         #                 }
#         #             }
#         #         }
#         #     }
#         # }
#         # mappings = {
#         #     "properties": {
#         #         "cleaned_address": {"type": "keyword"},
#         #         "original_address": {"type": "text"},
#         #         "formatted_address": {"type": "text"},
#         #     }
#         # }
#         # mappings = {
#         #     "properties": {
#         #         "cleaned_address": {"type": "text", "search_analyzer": "fingerprint"},
#         #         "original_address": {"type": "text"},
#         #         "formatted_address": {"type": "text"},
#         #         # "created": {
#         #         #     "type": "date",
#         #         #     "format": "strict_date_optional_time||epoch_millis"
#         #         # }
#         #     }
#         # }
#
#     class Django:
#         model = AddressComponent  # The model associated with this Document
#
#         # The fields of the model you want to be indexed in Elasticsearch
#         fields = [
#             'cleaned_address','original_address','formatted_address',
#             'extracted_original_address','extracted_formatted_address','created',
#         ]
#
#         # Ignore auto updating of Elasticsearch when a model is saved
#         # or deleted:
#         # ignore_signals = True
#
#         # Don't perform an index refresh after every update (overrides global setting):
#         # auto_refresh = False
#
#         # Paginate the django queryset used to populate the index with the specified size
#         # (by default it uses the database driver's default setting)
#         # queryset_pagination = 5000

# from elasticsearch_dsl.connections import connections
#
# connections.create_connection(hosts=['localhost'])


class AddressDocument(Document):
    # Create a mapping for index with properties:
    # cleaned_address is processed address by user-defined function, used as unique key
    cleaned_address = Text(analyzer='keyword')
    original_address = Text(analyzer='fingerprint')
    formatted_address = Text(analyzer='standard')
    extracted_original_address = Text(analyzer='fingerprint')
    extracted_formatted_address = Text(analyzer='fingerprint')
    long = Double()
    lat = Double()
    created = Date()

    class Index:
        # Name of the Elasticsearch index
        name = 'addresses'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0, }

    def save(self, **kwargs):
        self.created = datetime.now()
        return super(AddressDocument, self).save(**kwargs)
