#!/usr/bin/env python
"""
One-shot AURA batch for scheduled execution.

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

from aura.scripts.aura_worker import process_pending_sessions


def main():
    print(f"[{timezone.now()}] AURA scheduled batch started")
    process_pending_sessions()
    print(f"[{timezone.now()}] AURA scheduled batch finished")


if __name__ == "__main__":
    main()
