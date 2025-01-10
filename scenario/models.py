from django.db import models
from user.models import User

# Create your models here.
class Scenario(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=32, null=False)
    location = models.CharField(max_length=32, null=False)
    type = models.CharField(max_length=32, null=False)
    datetime = models.CharField(max_length=32, null=False)
    description = models.CharField(max_length=512, null=False)
    image = models.CharField(max_length=512, null=False)
    level = models.IntegerField(null=False)
    note = models.CharField(max_length=512, null=True)
    is_success = models.BooleanField(default=False, null=True)
    count = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False, null=True)

    class Meta:
        db_table = 'Scenario'