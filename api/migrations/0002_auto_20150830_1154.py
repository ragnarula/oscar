# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='_current_state',
        ),
        migrations.AddField(
            model_name='device',
            name='auto_connect',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='device',
            name='current_state',
            field=models.CharField(default=b'READY', max_length=10),
        ),
    ]
