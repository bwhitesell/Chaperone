# Generated by Django 2.1.7 on 2019-08-25 15:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('classifiers', '0003_modelperformance'),
    ]

    operations = [
        migrations.RenameField(
            model_name='modelperformance',
            old_name='log_loss_n_nr',
            new_name='log_loss_n_r',
        ),
    ]
