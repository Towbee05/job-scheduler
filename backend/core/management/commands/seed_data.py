import uuid
import random
from datetime import timedelta
from django.core.management import BaseCommand
from django.utils import timezone
from core.models import Job, JobDependency, PriorityChoice, StatusChoices, IntervalChoices

JOB_TYPES = ["send_email", "webhook_delivery", "log_processing", "data_export", "report_generation"]

EMAIL_PAYLOADS = [
    {"to": "alice@example.com", "subject": "Welcome to the platform", "body": "Hello Alice, welcome aboard!"},
    {"to": "bob@example.com", "subject": "Password reset", "body": "Click here to reset your password."},
    {"to": "carol@example.com", "subject": "Invoice attached", "body": "Your monthly invoice is ready."},
    {"to": "dave@example.com", "subject": "Account suspended", "body": "Your account has been temporarily suspended."},
    {"to": "eve@example.com", "subject": "New login detected", "body": "A new login was detected from an unrecognized device."},
]

WEBHOOK_PAYLOADS = [
    {"url": "https://api.example.com/webhooks/order_created", "event": "order.created", "data": {"order_id": "ORD-001", "total": 49.99}},
    {"url": "https://api.example.com/webhooks/user_signup", "event": "user.signup", "data": {"user_id": "USR-001"}},
    {"url": "https://hooks.example.com/alert", "event": "alert.critical", "data": {"service": "api-gateway", "error": "timeout"}},
    {"url": "https://api.example.com/webhooks/payment_failed", "event": "payment.failed", "data": {"transaction_id": "TXN-001", "reason": "insufficient_funds"}},
    {"url": "https://hooks.example.com/deploy", "event": "deploy.completed", "data": {"environment": "production", "version": "v2.1.0"}},
]

LOG_PAYLOADS = [
    {"source": "nginx", "level": "error", "message": "upstream timed out", "count": 12},
    {"source": "postgres", "level": "warning", "message": "connection pool exhausted", "count": 5},
    {"source": "redis", "level": "info", "message": "cache miss rate above 10%", "count": 87},
    {"source": "celery", "level": "error", "message": "task queue backlog detected", "count": 23},
    {"source": "app", "level": "critical", "message": "out of memory", "count": 1},
]

EXPORT_PAYLOADS = [
    {"format": "csv", "dataset": "users", "filters": {"active": True}, "destination": "s3://exports/users/"},
    {"format": "json", "dataset": "transactions", "filters": {"date": "2026-06-01", "date_end": "2026-06-10"}, "destination": "s3://exports/transactions/"},
    {"format": "parquet", "dataset": "analytics", "filters": {"month": "2026-05"}, "destination": "s3://exports/analytics/"},
    {"format": "xlsx", "dataset": "reports", "filters": {"department": "engineering"}, "destination": "sftp://backup/reports/"},
    {"format": "csv", "dataset": "orders", "filters": {"status": "pending_fulfillment"}, "destination": "s3://exports/orders/"},
]

REPORT_PAYLOADS = [
    {"type": "weekly_summary", "period": "2026-06-01 to 2026-06-07", "channels": ["email", "slack"]},
    {"type": "monthly_kpi", "period": "May 2026", "metrics": ["revenue", "active_users", "churn_rate"]},
    {"type": "error_breakdown", "period": "last_7_days", "group_by": "service"},
    {"type": "performance_report", "period": "last_24h", "metrics": ["p95_latency", "error_rate", "throughput"]},
    {"type": "audit_log", "period": "2026-06", "include": ["admin_actions", "config_changes"]},
]

TYPE_PAYLOAD_MAP = {
    "send_email": EMAIL_PAYLOADS,
    "webhook_delivery": WEBHOOK_PAYLOADS,
    "log_processing": LOG_PAYLOADS,
    "data_export": EXPORT_PAYLOADS,
    "report_generation": REPORT_PAYLOADS,
}


def random_payload(job_type):
    pool = TYPE_PAYLOAD_MAP.get(job_type, EMAIL_PAYLOADS)
    return random.choice(pool)


def create_jobs(num=55):
    now = timezone.now()
    jobs = []

    # --- Layer 1: Independent jobs (no dependencies) ---
    for i in range(30):
        job_type = random.choice(JOB_TYPES)
        scheduled_at = now + timedelta(
            seconds=random.randint(-300, 3600)
        )
        job = Job.objects.create(
            type=job_type,
            priority=random.choice([1, 2, 3]),
            mutated_priority=random.choice([1, 2, 3]),
            payload=random_payload(job_type),
            status=StatusChoices.PENDING if scheduled_at > now or random.random() > 0.3 else random.choice(
                [StatusChoices.COMPLETED, StatusChoices.FAILED, StatusChoices.CANCELLED]
            ),
            scheduled_at=scheduled_at,
            retry_count=random.choice([0, 0, 0, 1, 2]) if random.random() > 0.8 else 0,
            processed_at=now - timedelta(minutes=random.randint(1, 60)) if random.random() > 0.7 else None,
            interval=random.choice([None, None, None, "every_1_minute", "every_5_minutes"]) if random.random() > 0.85 else None,
        )
        jobs.append(job)

    # --- Layer 2: Jobs that form DAG chains ---
    # Chain 1: generate_report -> upload_file -> send_email
    report_job = Job.objects.create(
        type="report_generation",
        priority=1,
        mutated_priority=1,
        payload=random_payload("report_generation"),
        status=StatusChoices.COMPLETED,
        scheduled_at=now - timedelta(minutes=10),
        processed_at=now - timedelta(minutes=8),
    )
    jobs.append(report_job)

    upload_job = Job.objects.create(
        type="data_export",
        priority=2,
        mutated_priority=2,
        payload=random_payload("data_export"),
        status=StatusChoices.PENDING,
        scheduled_at=now - timedelta(minutes=5),
    )
    JobDependency.objects.create(parent_job=report_job, child_job=upload_job)
    jobs.append(upload_job)

    email_notify_job = Job.objects.create(
        type="send_email",
        priority=3,
        mutated_priority=3,
        payload={"to": "team@example.com", "subject": "Report ready", "body": "The monthly report is ready for review."},
        status=StatusChoices.PENDING,
        scheduled_at=now - timedelta(minutes=2),
    )
    JobDependency.objects.create(parent_job=upload_job, child_job=email_notify_job)
    jobs.append(email_notify_job)

    # Chain 2: log_processing -> webhook_alert (with a completed parent)
    log_job = Job.objects.create(
        type="log_processing",
        priority=2,
        mutated_priority=2,
        payload=random_payload("log_processing"),
        status=StatusChoices.COMPLETED,
        scheduled_at=now - timedelta(minutes=30),
        processed_at=now - timedelta(minutes=25),
    )
    jobs.append(log_job)

    webhook_alert_job = Job.objects.create(
        type="webhook_delivery",
        priority=1,
        mutated_priority=1,
        payload=random_payload("webhook_delivery"),
        status=StatusChoices.PENDING,
        scheduled_at=now - timedelta(minutes=20),
    )
    JobDependency.objects.create(parent_job=log_job, child_job=webhook_alert_job)
    jobs.append(webhook_alert_job)

    # Chain 3: Three-level DAG with multiple parents
    data_prep = Job.objects.create(
        type="log_processing",
        priority=3,
        mutated_priority=3,
        payload=random_payload("log_processing"),
        status=StatusChoices.COMPLETED,
        scheduled_at=now - timedelta(minutes=60),
        processed_at=now - timedelta(minutes=55),
    )
    jobs.append(data_prep)

    validate_data = Job.objects.create(
        type="data_export",
        priority=3,
        mutated_priority=3,
        payload=random_payload("data_export"),
        status=StatusChoices.COMPLETED,
        scheduled_at=now - timedelta(minutes=45),
        processed_at=now - timedelta(minutes=40),
    )
    jobs.append(validate_data)

    merge_job = Job.objects.create(
        type="report_generation",
        priority=2,
        mutated_priority=2,
        payload=random_payload("report_generation"),
        status=StatusChoices.PENDING,
        scheduled_at=now - timedelta(minutes=30),
    )
    JobDependency.objects.create(parent_job=data_prep, child_job=merge_job)
    JobDependency.objects.create(parent_job=validate_data, child_job=merge_job)
    jobs.append(merge_job)

    final_email = Job.objects.create(
        type="send_email",
        priority=1,
        mutated_priority=1,
        payload={"to": "stakeholders@example.com", "subject": "Merged report", "body": "The merged analysis is ready."},
        status=StatusChoices.PENDING,
        scheduled_at=now - timedelta(minutes=20),
    )
    JobDependency.objects.create(parent_job=merge_job, child_job=final_email)
    jobs.append(final_email)

    # --- Layer 3: Burst of unique jobs for entropy ---
    for i in range(12):
        job_type = random.choice(JOB_TYPES)
        job = Job.objects.create(
            type=job_type,
            priority=random.choice([1, 2, 3]),
            mutated_priority=random.choice([1, 2, 3]),
            payload=random_payload(job_type),
            status=StatusChoices.PENDING,
            scheduled_at=now + timedelta(seconds=random.randint(-60, 600)),
            retry_count=0,
            interval=random.choice([None, None, None, None, "every_1_hour"]) if i % 4 == 0 else None,
        )
        jobs.append(job)

    return jobs


class Command(BaseCommand):
    help = "Seed the database with 50+ varied jobs for testing"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database with 50+ jobs...")
        created = create_jobs(55)
        total = len(created)
        counts = {label: Job.objects.filter(status=label).count() for label in ["pending", "processing", "completed", "failed", "cancelled"]}
        dep_count = JobDependency.objects.count()
        self.stdout.write(f"Created {total} jobs")
        self.stdout.write(f"Statuses: {counts}")
        self.stdout.write(f"Dependencies: {dep_count}")
        self.stdout.write("Seeding complete.")
