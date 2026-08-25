
from django.db import migrations
import os
from cryptography.fernet import Fernet

def get_fernet():
    return Fernet(os.environ['ENCRYPTION_KEY'].encode())

def encrypt_existing(apps, schema_editor):
    fernet = get_fernet()  # initialize here, not at module level
    Questions = apps.get_model('teachers', 'Questions')

    for q in Questions.objects.using(schema_editor.connection.alias).iterator(chunk_size=500):
        if not q.question:
            continue
        try:
            fernet.decrypt(q.question.encode())  # already encrypted, skip
        except Exception:
            q.question = fernet.encrypt(q.question.encode()).decode()
            q.save(update_fields=['question'])

def decrypt_all(apps, schema_editor):
    fernet = get_fernet()
    Questions = apps.get_model('teachers', 'Questions')

    for q in Questions.objects.using(schema_editor.connection.alias).iterator(chunk_size=500):
        if not q.question:
            continue
        try:
            decrypted = fernet.decrypt(q.question.encode()).decode()
            q.question = decrypted
            q.save(update_fields=['question'])
        except Exception:
            pass  # already plain text, skip

class Migration(migrations.Migration):
    dependencies = [
       ('teachers', '0036_alter_questions_question'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing, reverse_code=decrypt_all),
    ]
