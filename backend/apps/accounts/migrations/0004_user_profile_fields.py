from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_groups_alter_user_is_superuser_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="phone",
            field=models.CharField(blank=True, max_length=32, verbose_name="Телефон"),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to="avatars/", verbose_name="Аватар"),
        ),
        migrations.AddField(
            model_name="user",
            name="bio",
            field=models.TextField(blank=True, max_length=500, verbose_name="О себе"),
        ),
        migrations.AddField(
            model_name="user",
            name="birth_date",
            field=models.DateField(blank=True, null=True, verbose_name="Дата рождения"),
        ),
        migrations.AddField(
            model_name="user",
            name="country",
            field=models.CharField(blank=True, max_length=80, verbose_name="Страна"),
        ),
        migrations.AddField(
            model_name="user",
            name="city",
            field=models.CharField(blank=True, max_length=80, verbose_name="Город"),
        ),
        migrations.AddField(
            model_name="user",
            name="address",
            field=models.CharField(blank=True, max_length=255, verbose_name="Адрес"),
        ),
        migrations.AddField(
            model_name="user",
            name="telegram",
            field=models.CharField(blank=True, max_length=64, verbose_name="Telegram"),
        ),
        migrations.AddField(
            model_name="user",
            name="newsletter",
            field=models.BooleanField(default=False, verbose_name="Подписан на рассылку"),
        ),
    ]
