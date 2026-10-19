import uuid
import math
from django.db import models
from django.db.models import Q
from django.utils import timezone

class Spot(models.Model):
    label = models.CharField(max_length=12, unique=True)
    class Meta:
        ordering = ['label']

class Visit(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    request_id = models.UUIDField(unique=True)
    spot = models.ForeignKey(Spot, on_delete=models.PROTECT)
    owner = models.CharField(max_length=100)
    plate = models.CharField(max_length=20)
    car_model = models.CharField(max_length=80)
    color = models.CharField(max_length=40)
    entered_at = models.DateTimeField(default=timezone.now)
    exited_at = models.DateTimeField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['spot'], condition=Q(exited_at__isnull=True), name='one_active_visit_per_spot'), models.UniqueConstraint(fields=['plate'], condition=Q(exited_at__isnull=True), name='one_active_visit_per_plate')]
    def hours(self, at=None):
        return max(1, math.ceil(((self.exited_at or at or timezone.now()) - self.entered_at).total_seconds() / 3600))
    def bill(self, at=None):
        return self.hourly_rate * self.hours(at)
