from django.db import migrations

def migrate_data_forward(apps, schema_editor):
    Tests = apps.get_model('teachers', 'Tests')
    Standard = apps.get_model('teachers', 'Standard')
    Subject = apps.get_model('teachers', 'Subject')
    
    for test in Tests.objects.all():
        # Migrate standard
        if test.standard:
            try:
                standard_obj = Standard.objects.get(standard=test.standard)
                test.choose_standard = standard_obj
            except Standard.DoesNotExist:
                print(f"ERROR: Standard {test.standard} not found for test {test.id}")
                continue
        
        # Migrate subject
        if test.subject:
            try:
                subject_obj = Subject.objects.get(name=test.subject)
                test.choose_subject = subject_obj
            except Subject.DoesNotExist:
                print(f"ERROR: Subject '{test.subject}' not found for test {test.id}")
                continue
        
        test.save()

def migrate_data_backward(apps, schema_editor):
    Tests = apps.get_model('teachers', 'Tests')
    
    for test in Tests.objects.all():
        if test.choose_standard:
            test.standard = test.choose_standard.standard
        if test.choose_subject:
            test.subject = test.choose_subject.name
        test.save()

class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0028_populate_subject_standard_tables'),
    ]

    operations = [
        migrations.RunPython(migrate_data_forward, migrate_data_backward),
    ]