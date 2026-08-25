from .sse_store import broadcast

def activate_test(test_id):
    from django_q.tasks import schedule
    from django_q.models import Schedule
    import datetime

    from .models import Tests
    
    try:
        test = Tests.objects.get(pk=test_id)
        test.isActive = True
        test.activated_at = datetime.datetime.now()
        test.save()
        broadcast(test, test.user.institute, test.standard)

        Schedule.objects.filter(name=f'deactivate-test-{test_id}').delete()
        schedule(
            'teachers.tasks.deactivate_test',
            test_id,
            schedule_type=Schedule.ONCE,
            next_run=test.activated_at + test.time,  # DurationField adds directly to datetime
            name=f'deactivate-test-{test_id}',
        )
    except Tests.DoesNotExist:
        pass


def deactivate_test(test_id):
    from .models import Tests
    try:
        test = Tests.objects.get(pk=test_id)
        if test.isActive:
            test.isActive = False
            test.activated_at = None
            test.readOnly = True
            test.save()
            broadcast(test, test.user.institute, test.standard, 'deactivate')

    except Tests.DoesNotExist:
        pass