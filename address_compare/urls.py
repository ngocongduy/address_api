# from django.urls import path
from . import views
#
# urlpatterns = [
#     path('', views.index, name='index'),
#     path('', views.index, name='index'),
# ]

from django.conf.urls import url
urlpatterns = [
    # home
    url(r'^$', views.index, name='index'),
    # api
    url(r'^api/v1/compare/$', views.post_address_compare , name='post_address_compare'),
    url(r'^api/v1/compare-list/$', views.post_address_compare_list , name='post_address_compare_list'),
    # url(r'^api/v1/locate-async/$', views.async_post_address_locate , name='async_post_address_locate'),
    # url(r'^api/v1/save/$', views.save_data_elastic_search , name='save_data_elastic_search'),
    # url(r'^api/v1/search/$', views.search_address , name='search_address'),
    # url(r'^api/v1/compare-address/$', views.compare_addresses , name='compare_addresses'),
]
