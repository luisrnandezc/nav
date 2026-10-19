# FPT backend actions

These routes use Django session authentication and CSRF protection, like the
aircraft Scheduler. Action responses are JSON. The calendar page at
`/scheduler/fpt/` uses the shared `ui` styles and the Scheduler's calendar design.

The dashboard tile uses the same view permission policy. Managers can click a
free start to reserve or lock it, or click occupied hours to edit, reschedule,
change payment status, or delete occupancy. Viewers can open read-only details.
Period navigation includes open and closed periods. The calendar groups dates
into seven-day tables, with horizontal scrolling on narrow screens, and shows
both occupied hours of each session. A free hour which cannot accommodate a
complete two-hour session is marked as having no available start.

All paths below are under `/scheduler/fpt/`.

| Path | GET | POST |
| --- | --- | --- |
| `periods/` | List periods, categories, statuses, `can_manage` | Create a period |
| `periods/<id>/` | Period, sessions, daily available starting hours | Edit dates or open/close |
| `periods/<id>/delete/` | — | Delete an empty period |
| `sessions/create/` | — | Create a reservation or administrative lock |
| `sessions/<id>/` | Read one session | Edit, reschedule, change payment status or convert to/from a lock |
| `sessions/<id>/delete/` | — | Remove occupancy |
| `participants/` | Registered student/instructor IDs and names (managers only) | — |
| `history/?object_type=session&object_id=<id>` | Latest 100 audit entries (managers only; also accepts `period`) | — |

Readers require `scheduler.view_fpt_schedule`; managers require
`scheduler.manage_fpt_schedule`, which includes reading. Both policies require
an active user with role `STAFF` or `INSTRUCTOR`. Students cannot access these
actions even if they have either permission. Anonymous requests redirect to login.

POST accepts a JSON object or normal Django form data. Send the usual CSRF token.
Every edit and delete must include `expected_updated_at`, copied exactly from
the most recent GET response's `updated_at`. The server compares it under the
row lock; missing versions return 400, stale versions return 409 with
`code: stale_edit`. The calendar preserves unsaved inputs and offers an explicit
reload action; it never silently retries a stale write with a newer version.
Edits accept only changed fields and preserve omitted fields, including boolean
values. Explicitly send `is_active: false` to close a period. Unknown fields and
nested inputs are rejected. Omitted `is_active` on creation defaults to false.

Period creation fields: `start_date`, `end_date` (ISO dates), optional `is_active`.
Periods must start on Monday and end on Sunday, lasting 7, 14, 21, or 28 days.
Both model validation and database constraints enforce the weekday boundaries.
Session creation fields: `period` (ID), `date`, `start_hour` (integer 8–18),
`status` (`pending`, `paid`, `locked`), and optional `notes`.
Reservations additionally require `category` (`HVI`, `HVI-R`, `ENT`, `CA`, `PC`,
`OTHER`) and exactly one of `student` (ID) / `external_student_name`, and exactly
one of `instructor` (ID) / `external_instructor_name`.

Locks require blank category and no participants. When converting a reservation
to a lock, explicitly clear all participant fields and category. When switching
between registered and external participants, clear the previous assignment.

Session responses include participant IDs, external names, display names,
category/status labels, and derived `start_time`/`end_time`. No participant email
or national ID is exposed. Payment status is set manually; no financial records
or aircraft scheduling records are modified.

Availability covers every inclusive date of a period and starting hours 08–18.
Each candidate occupies two hours; adjacent sessions are allowed. Closed periods
return no available starts but retain their sessions. Availability is advisory:
every save revalidates and the database prevents overlapping occupancy.

Validation failures return HTTP 400 with `error` and field `errors`; permission
failures return 403. Missing objects return 404, unsupported methods 405, successful
creates 201, and other successful actions 200. A database conflict returns 409 with
a refresh/retry message. Deleting a period with sessions also returns 409.

Period and session edits lock the current row in a transaction on PostgreSQL.
The model also locks the destination period before saving occupancy. Database
conflicts are caught outside the transaction, after rollback. SQLite busy-writer
errors return 409; unrelated database failures are not disguised as conflicts.

Closing a period prevents new bookings/rescheduling and conversion of locks to
reservations. Payment/notes corrections and removing occupancy remain allowed.
There is no student/instructor availability or account-balance check.

Every successful period/session create, update, or delete through these actions
also stores an FPT audit entry in the same transaction. It records the actor,
timestamp, action, and before/after snapshots (including manual payment changes).
Entries retain object IDs and actor display names after deletion. Failed writes
leave no audit entry; an audit failure rolls back the scheduling change.

## Release checks

Migration `0025_fpt_release_hardening` checks existing periods first. If any have
non-Monday/Sunday boundaries it reports their IDs and stops without rewriting
dates or reservations. Correct those periods deliberately before retrying. The
migration reinstalls overlap guards after SQLite table rebuilds and supports
rollback/reapplication. Rolling it back removes the audit table and its history.

CI runs backend tests on SQLite and PostgreSQL 17, then executes Chromium
regressions on both. Locally, install `requirements-test.txt`, run
`python -m playwright install chromium`, then from `config/` run:

```powershell
$env:RUN_FPT_BROWSER_TESTS = '1'
python manage.py test scheduler.test.test_fpt_browser --noinput
```

Browser tests use a disposable Django live-server database and authenticated
test accounts. They cover booking, external participants, rescheduling, payment,
locks, stale dialogs, period boundaries, read-only access, and mobile controls.
Normal backend test runs skip browser tests unless explicitly enabled.
