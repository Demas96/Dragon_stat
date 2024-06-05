from django.contrib.auth.models import User
from django.db import models


class APIkeys(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    api_key = models.TextField()
    api_secret = models.TextField()


class Balance(models.Model):
    total_balance = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, )
    balance = models.ForeignKey(Balance, on_delete=models.CASCADE,)
