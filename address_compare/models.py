from django.db import models


# Create your models here.

class AddressRequest(models.Model):
    address_source = models.CharField(max_length=200)
    address_compare = models.CharField(max_length=200)

