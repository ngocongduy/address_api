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
]