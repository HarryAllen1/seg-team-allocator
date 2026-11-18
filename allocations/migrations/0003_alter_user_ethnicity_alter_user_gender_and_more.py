from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocations', '0002_user_profile_team'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='ethnicity',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, 'Not provided'),
                    (1, 'Asian, or Asian British'),
                    (2, 'Black, Black British, Caribbean, or African'),
                    (3, 'Mixed, or multiple ethnic groups'),
                    (4, 'White'),
                    (5, 'Other ethnic group (e.g. Arab)'),
                ],
                default=0,
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='gender',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, 'Not provided'),
                    (1, 'Woman'),
                    (2, 'Man'),
                    (3, 'Other/Non-binary'),
                ],
                default=0,
            ),
        ),
    ]
