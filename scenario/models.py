from django.db import models
from Backend.user.models import User

# Create your models here.
class Scenario(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    location = models.CharField(max_length=32)
    type = models.CharField(max_length=32)
    datetime = models.CharField(max_length=32)
    description = models.CharField(max_length=512)
    image = models.CharField(max_length=512)
    level = models.IntegerField()
    note = models.CharField(max_length=512)
    is_success = models.BooleanField(default=False)
    count = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Scenario'