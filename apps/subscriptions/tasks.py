from celery import shared_task
from django.utils import timezone
from apps.subscriptions.models import Subscription
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_expired_subscriptions():
    """
    Celery Beat দ্বারা পরিচালিত শিডিউল টাস্ক:
    প্রতিদিন মেয়াদোত্তীর্ণ ট্রায়াল ও অ্যাক্টিভ সাবস্ক্রিপশন চেক করে স্ট্যাটাস আপডেট করবে
    """
    now = timezone.now()

    # ১. যেসব টেন্যান্টের ট্রায়ালের মেয়াদ শেষ হয়ে গেছে
    expired_trials = Subscription.objects.filter(status='trial', trial_end__lte=now)
    trial_count = expired_trials.update(status='expired')

    # ২. যেসব অ্যাক্টিভ সাবস্ক্রিপশনের বিলিং পিরিয়ড শেষ
    overdue_subscriptions = Subscription.objects.filter(status='active', current_period_end__lte=now)
    overdue_count = overdue_subscriptions.update(status='past_due')

    logger.info(f"Subscription audit complete: {trial_count} trials expired, {overdue_count} marked past due.")
    return f"Processed: {trial_count} expired, {overdue_count} past-due"