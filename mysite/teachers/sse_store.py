# sse_store.py
from .models import TestEvent

def broadcast(test, institute, standard, message='activate'):
    TestEvent.objects.create(
        test=test,
        institute=institute,
        standard=standard,
        message=message
    )