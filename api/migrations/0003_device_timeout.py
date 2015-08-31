# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20150830_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='timeout',
            field=models.IntegerField(default=0),
        ),
    ]
