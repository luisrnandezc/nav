#!/usr/bin/env python
"""
One-shot SMS AI batch for scheduled execution.

Use this with a PythonAnywhere scheduled task. It boots Django, processes
pending SMS reports once, and exits.
"""

import os
import sys

import django


project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, "..", "..")
sys.path.insert(0, django_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone

from sms.scripts.sara_worker import process_pending_reports


def main():
    print(f"[{timezone.now()}] SMS scheduled batch started")
    process_pending_reports()
    print(f"[{timezone.now()}] SMS scheduled batch finished")


if __name__ == "__main__":
    main()
