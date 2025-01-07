from django.db import models
from scenario.models import Scenario

# Create your models here.
class Evidence(models.Model):
    id = models.AutoField(primary_key=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    name = models.CharField(max_length=16)
    description = models.CharField(max_length=512)
    image = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Evidence'