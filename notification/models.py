from django.db import models
from authentication.models import BaseModel,CustomUser

# Create your models here.

class Notifications(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    notification = models.CharField(max_length=1000)
    is_seen = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.notification}'

    class Meta:
        verbose_name_plural = 'Notifications'