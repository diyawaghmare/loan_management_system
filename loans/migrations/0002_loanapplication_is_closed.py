# Generated by Django 4.2.13 on 2024-06-12 18:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("loans", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="loanapplication",
            name="is_closed",
            field=models.BooleanField(default=False),
        ),
    ]