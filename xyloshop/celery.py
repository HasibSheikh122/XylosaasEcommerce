import os
from celery import Celery

# Django settings মডিউল সেট করা
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xyloshop.settings')

app = Celery('xyloshop')

# settings.py থেকে CELERY_ প্রিফিক্স থাকা সব কনফিগারেশন লোড করা
app.config_from_object('django.conf:settings', namespace='CELERY')

# সব অ্যাপের tasks.py অটোমেটিক স্ক্যান ও লোড করা
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')