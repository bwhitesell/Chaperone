# Generated by Django 2.1.7 on 2019-05-13 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crime', '0006_auto_20190513_0145'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrimesPremisesVolume',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('premis_desc', models.TextField()),
                ('volume', models.IntegerField()),
            ],
        ),
    ]
