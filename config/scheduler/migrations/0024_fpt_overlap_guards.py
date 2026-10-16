"""Protect the single FPT even when concurrent requests both pass clean().

PostgreSQL range exclusions need no extension because each constraint compares
one range only. SQLite serializes writes; triggers reject conflicting occupancy.
Keep these guards in sync if the FPT tables are renamed or rebuilt.
"""

from django.db import migrations


def add_guards(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        schema_editor.execute("""
            ALTER TABLE scheduler_fptperiod ADD CONSTRAINT fpt_period_no_overlap
            EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
        """)
        schema_editor.execute("""
            ALTER TABLE scheduler_fptsession ADD CONSTRAINT fpt_session_no_overlap
            EXCLUDE USING gist (
                int8range(
                    (date - DATE '2000-01-01')::bigint * 24 + start_hour,
                    (date - DATE '2000-01-01')::bigint * 24 + start_hour + 2,
                    '[)'
                ) WITH &&
            )
        """)
    elif vendor == 'sqlite':
        for operation in ('INSERT', 'UPDATE'):
            schema_editor.execute(f"""
                CREATE TRIGGER fpt_period_no_overlap_{operation.lower()}
                BEFORE {operation} ON scheduler_fptperiod
                WHEN EXISTS (
                    SELECT 1 FROM scheduler_fptperiod p
                    WHERE p.id != NEW.id AND p.start_date <= NEW.end_date
                    AND p.end_date >= NEW.start_date
                )
                BEGIN SELECT RAISE(ABORT, 'fpt_period_no_overlap'); END
            """)
            schema_editor.execute(f"""
                CREATE TRIGGER fpt_session_no_overlap_{operation.lower()}
                BEFORE {operation} ON scheduler_fptsession
                WHEN EXISTS (
                    SELECT 1 FROM scheduler_fptsession s
                    WHERE s.id != NEW.id AND s.date = NEW.date
                    AND s.start_hour < NEW.start_hour + 2
                    AND s.start_hour + 2 > NEW.start_hour
                )
                BEGIN SELECT RAISE(ABORT, 'fpt_session_no_overlap'); END
            """)
    else:
        raise RuntimeError('FPT overlap protection supports PostgreSQL and SQLite only.')


def remove_guards(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(
            'ALTER TABLE scheduler_fptsession DROP CONSTRAINT fpt_session_no_overlap'
        )
        schema_editor.execute(
            'ALTER TABLE scheduler_fptperiod DROP CONSTRAINT fpt_period_no_overlap'
        )
    elif schema_editor.connection.vendor == 'sqlite':
        for table in ('period', 'session'):
            for operation in ('insert', 'update'):
                schema_editor.execute(f'DROP TRIGGER fpt_{table}_no_overlap_{operation}')


class Migration(migrations.Migration):
    dependencies = [('scheduler', '0023_fpt_models')]
    operations = [migrations.RunPython(add_guards, remove_guards)]
