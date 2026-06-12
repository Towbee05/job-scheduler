from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
class PriorityChoice(models.IntegerChoices):
    HIGH = 1, _("HIGH")
    MEDIUM = 2, _("MEDIUM")
    LOW = 3, _("LOW")

class StatusChoices(models.TextChoices):
    PENDING = "pending", _("PENDING")
    PROCESSING = "processing", _("PROCESSING")
    COMPLETED = "completed", _("COMPLETED")
    FAILED ="failed", _("FAILED")
    CANCELLED = "cancelled", _("CANCELLED")

class IntervalChoices(models.TextChoices):
    MINUTE_1 = "every_1_minute", _("Every 1 min")
    MINUTE_5 = "every_5_minutes", _("Every 5 mins")
    HOUR_1 = "every_1_hour", _("Every 1 hour")


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(null=False, blank=False, max_length=255)
    priority = models.IntegerField(choices=PriorityChoice, default=PriorityChoice.LOW)
    mutated_priority = models.IntegerField(choices=PriorityChoice, default=PriorityChoice.LOW)
    payload = models.JSONField()
    status = models.CharField(choices=StatusChoices, default=StatusChoices.PENDING, max_length=120)
    scheduled_at = models.DateTimeField(null=False, blank=False, default=timezone.now)
    retry_count = models.IntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    interval = models.CharField(max_length=50, null=True, blank=True, choices=IntervalChoices)
    is_cancel_requested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dependencies = models.ManyToManyField("self", through="JobDependency", symmetrical=False, blank=True, related_name="dependent_jobs")

    def __str__(self):
        return self.type

class JobDependency(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    parent_job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="as_parent") # jobs that must be completed first
    child_job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="as_child") # jobs that wait till this is completed

    class Meta:
        unique_together = ("parent_job", "child_job")
    
    def __str__(self):
        return str(self.id)

class DeadLetterQueue(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    job = models.OneToOneField(Job, on_delete=models.CASCADE)
    error = models.TextField()
    failed_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)