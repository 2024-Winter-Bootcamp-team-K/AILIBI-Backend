from django.db import models
from scenario.models import Scenario

# Create your models here.
class Suspect(models.Model):
    GENDER_CHOICES = [
        (0, '남성'),
        (1, '여성'),
    ]

    THEIF_CHOICES = [
        (0, '무고한 시민'),
        (1, '범인'),
    ]

    id = models.AutoField(primary_key=True, null=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=16, null=False)
    gender = models.BooleanField(choices=GENDER_CHOICES, null=False)
    age = models.IntegerField(null=False)
    job = models.CharField(max_length=16, null=False)
    description = models.CharField(max_length=512, null=True)
    init_chat = models.TextField(blank=True)
    is_theif = models.BooleanField(choices=THEIF_CHOICES, null=False)
    image = models.CharField(max_length=512, null=False)
    task_id = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False, null=True)

    class Meta:
        db_table = 'Suspect'