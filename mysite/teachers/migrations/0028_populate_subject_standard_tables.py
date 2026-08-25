from django.db import migrations
from django.utils import translation

def populate_tables(apps, schema_editor):
    Tests = apps.get_model('teachers', 'Tests')
    Standard = apps.get_model('teachers', 'Standard')
    Subject = apps.get_model('teachers', 'Subject')
    Institute = apps.get_model('accounts', 'Institute')
    
    # Get all unique subjects from Tests
    unique_subjects = Tests.objects.values_list('subject', flat=True).distinct()

    print(unique_subjects)
    translation.activate('en')
    for subject_name in unique_subjects:
        if subject_name:  # Skip empty/null values
            Subject.objects.get_or_create(name=subject_name, name_en=subject_name)
    
    # Get all unique standards from Tests
    unique_standards = Tests.objects.values_list('standard', flat=True).distinct()
    
    print(unique_standards)
    # You need to specify which institute these standards belong to
    # Option 1: Get a default institute
    try:
        default_institute = Institute.objects.first()
        if not default_institute:
            print("ERROR: No institute found. Please create at least one institute first.")
            return
    except:
        print("ERROR: Institute model issue")
        return
    
    for standard_value in unique_standards:
        if standard_value:  # Skip empty/null values
            Standard.objects.get_or_create(
                standard=standard_value,
                defaults={'institute': default_institute}
            )

def reverse_populate(apps, schema_editor):
    # Optional: clean up if migration is reversed
    Standard = apps.get_model('teachers', 'Standard')
    Subject = apps.get_model('teachers', 'Subject')
    
    # Be careful with this - only delete if you're sure
    # Standard.objects.all().delete()
    # Subject.objects.all().delete()
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0027_subject_name_en_subject_name_hi_subject_name_mr'),
    ]

    operations = [
        migrations.RunPython(populate_tables, reverse_populate),
    ]