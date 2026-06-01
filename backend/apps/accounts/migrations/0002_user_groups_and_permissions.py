# Add M2M groups and user_permissions (after auth tables exist)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="groups",
            field=models.ManyToManyField(blank=True, related_name="accounts_user_set", to="auth.group"),
        ),
        migrations.AddField(
            model_name="user",
            name="user_permissions",
            field=models.ManyToManyField(blank=True, related_name="accounts_user_set", to="auth.permission"),
        ),
    ]
