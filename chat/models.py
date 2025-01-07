from django.db import models
from Backend.suspect.models import Suspect

# Create your models here.
class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    suspect = models.ForeignKey(Suspect, on_delete=models.CASCADE)
    init_chat = models.CharField(max_length=1024)
    user_chat = models.CharField(max_length=1024)
    suspect_chat = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Chat'