from django.db import models
from scenario.models import Scenario

# Create your models here.
class Evidence(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=16, null=False)
    description = models.CharField(max_length=512, null=False)
    image = models.CharField(max_length=512, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False, null=True)

    class Meta:
        db_table = 'Evidence'