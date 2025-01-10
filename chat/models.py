from django.db import models
from suspect.models import Suspect

# Create your models here.
class Chat(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    suspect = models.ForeignKey(Suspect, on_delete=models.CASCADE, null=False)
    init_chat = models.TextField(blank=True, null=False)
    user_chat = models.TextField(blank=True, null=True)
    suspect_chat = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False, null=True)

    class Meta:
        db_table = 'Chat'