from django.db import models
from Backend.scenario.models import Scenario

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

    id = models.AutoField(primary_key=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    name = models.CharField(max_length=16)
    gender = models.BooleanField(choices=GENDER_CHOICES)
    age = models.IntegerField()
    job = models.CharField(max_length=16)
    personality = models.CharField(max_length=32)
    is_theif = models.BooleanField(choices=THEIF_CHOICES)
    image = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Suspect'