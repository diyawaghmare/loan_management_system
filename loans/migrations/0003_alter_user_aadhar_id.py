# Generated by Django 4.2.13 on 2024-06-13 09:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("loans", "0002_loanapplication_is_closed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="aadhar_id",
            field=models.CharField(max_length=36, unique=True),
        ),
    ]
