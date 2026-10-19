"""Database contention outcomes understood by FPT actions and race tests."""


def is_retryable_fpt_conflict(error, vendor):
    if vendor == 'sqlite':
        return 'locked' in str(error).lower()
    if vendor == 'postgresql':
        # Django preserves the driver exception as __cause__. psycopg2 exposes
        # pgcode; psycopg3 exposes sqlstate. Do not match translated error text
        # or swallow unrelated OperationalErrors such as connection failures.
        cause = error.__cause__
        code = getattr(cause, 'sqlstate', None) or getattr(cause, 'pgcode', None)
        return code == '40P01'  # deadlock_detected; the failed transaction rolls back.
    return False
