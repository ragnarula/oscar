# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('name', models.CharField(max_length=20, serialize=False, primary_key=True)),
                ('host', models.CharField(max_length=30)),
                ('port', models.CharField(max_length=5)),
                ('_current_state', models.CharField(max_length=10)),
            ],
        ),
    ]
