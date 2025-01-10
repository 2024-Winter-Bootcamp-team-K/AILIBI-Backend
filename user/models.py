from django.db import models

# Create your models here.
class User(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    name = models.CharField(max_length=16, null=False)
    email = models.EmailField(unique=True, max_length=32, null=False)
    password = models.CharField(max_length=64 ,null=False)
    created_at = models.DateTimeField(auto_now_add=True ,null=False)
    updated_at = models.DateTimeField(auto_now=True ,null=True)
    is_deleted = models.BooleanField(default=False, null=True)

    class Meta:
        db_table = 'User'