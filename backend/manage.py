#!/usr/bin/env python
"""
Plugin-local Django management entry point.

This is **only** used for running tooling against the plugin in isolation
(e.g. `./manage.py makemigrations registration_demographics`). In a real
deployment, the plugin runs inside `edx-platform` and you'd use the
platform's `manage.py lms ...` instead.
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Did you `make install` first?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
