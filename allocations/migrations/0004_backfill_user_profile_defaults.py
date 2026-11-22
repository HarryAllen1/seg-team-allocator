from django.db import migrations


def backfill_user_profile_defaults(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "UPDATE allocations_user SET ethnicity = 0 "
            "WHERE ethnicity = '' OR ethnicity IS NULL"
        )
        cursor.execute(
            "UPDATE allocations_user SET gender = 0 "
            "WHERE gender = '' OR gender IS NULL"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('allocations', '0003_alter_user_ethnicity_alter_user_gender_and_more'),
    ]

    operations = [
        migrations.RunPython(
            backfill_user_profile_defaults,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
