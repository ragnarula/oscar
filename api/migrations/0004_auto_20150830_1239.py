# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_device_timeout'),
    ]

    operations = [
        migrations.RenameField(
            model_name='device',
            old_name='auto_connect',
            new_name='active',
        ),
    ]
