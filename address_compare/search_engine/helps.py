from elasticsearch_dsl import Q, analyzer, Index
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


# client = Elasticsearch()
# s = Search(using=client)

# from django.conf import settings
#
# elastic_url = getattr(settings, "GOOGLE_API_KEY", '')

class AddressElasticSearchService:
    def __init__(self, document_class_name, query, size):
        self.query = query
        self.size = size
        self.search_instance = document_class_name.search()

    def run_query_list(self, cut_off_score=0):

        # bool to combine logics come next params, for instances: must a and must not b
        q = Q('bool', must=[Q('match', cleaned_address=self.query), ])
        print(q)
        # self.index_instance.
        # my_analyzer = analyzer('my_analyzer',
        #                        tokenizer=tokenizer('trigram', 'nGram', min_gram=3, max_gram=3),
        #                        filter=['lowercase']
        #                        )
        # custom_analyzer = analyzer({
        #     "my_fingerprint_analyzer": {
        #         "type": "fingerprint"}})
        # print(custom_analyzer)
        #
        # index = Index("addresses")
        # index.analyzer(custom_analyzer)
        # print(index.analyzer)
        search_with_query = self.search_instance.query(q).sort('_score')[0:self.size]
        # search_with_query = index.search().query(q).sort('_score')[0:self.size]

        print(type(self.search_instance))
        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits']
        if 0 < cut_off_score <= 1:
            result = [e for e in result if e.get('_score', 1) >= cut_off_score]
        elif cut_off_score == 0:
            pass
        return result


class SearchHelper:
    def __init__(self, index_name):
        self._client = Elasticsearch()
        self._search = Search(using=self._client,index=index_name)

    def query(self, query_body, size):
        search_with_query = self._search.query(query_body).sort('_score')
        print(search_with_query.to_dict())
        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits'][0:size]
        return result
