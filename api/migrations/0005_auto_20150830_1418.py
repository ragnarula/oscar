# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20150830_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='timeout',
            field=models.IntegerField(default=None, null=True, blank=True),
        ),
    ]
