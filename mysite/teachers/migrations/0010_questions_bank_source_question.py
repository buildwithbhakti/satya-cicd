from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("teachers", "0009_alter_questions_question_type_matchitem_matchpair"),
    ]

    operations = [
        migrations.AddField(
            model_name="questions",
            name="bank_source_question",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bank_copies",
                to="teachers.questions",
            ),
        ),
        migrations.AddField(
            model_name="questions",
            name="is_customized",
            field=models.BooleanField(default=False),
        ),
    ]

