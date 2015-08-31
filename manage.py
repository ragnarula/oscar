#!/usr/bin/env python
from gevent import monkey; monkey.patch_all(thread=False)
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oscar.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
