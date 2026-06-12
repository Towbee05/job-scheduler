from django.utils.translation import gettext_lazy as _
import logging
import random
import time

logger = logging.getLogger(__name__)
class Handler:
    def __init__(self):
        self.default_email_body = '''
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer ac blandit leo. Donec quis nibh nec elit tincidunt facilisis et non enim. Ut dictum finibus nisi at faucibus. Donec cursus.
'''
    def simulate_email_delivery(self, job_id, payload):
        email_payload = payload
        
        required_fields = ["to", "subject"]
        for field in required_fields:
            if email_payload.get(field) is None:
                raise ValueError(_(f"{field} is required in payload"))
            
        to = email_payload.get("to")
        subject = email_payload.get("subject")
        body = email_payload.get("body", self.default_email_body)

        logger.info("Email handler start", extra={
            "job_id": job_id,
            "to": to,
            "subject": subject
        })

        # simulate email delivery with 40% failure rate
        failure_probability = random.random()
        logger.info("probability to fail", extra={"random": failure_probability})
        if failure_probability < 0.4:
            logger.info("simulated failure to send email", extra={"job_id": job_id})
            raise Exception(f"Simulation of email failure to {to}")
        
        # Let email process for 2-6 seconds
        sleep = random.uniform(2, 6)
        time.sleep(sleep)
        logger.info("Email handler success", extra={"job_id": job_id, "to": to, "subject": subject, "body": body})
        return {"status": "completed", "job_id": job_id, "to": to, "subject": subject, "body": body}