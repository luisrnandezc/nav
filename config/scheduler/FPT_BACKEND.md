# FPT backend actions

These routes use Django session authentication and CSRF protection, like the
aircraft Scheduler. Responses are JSON; no frontend is included yet.

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

Readers require `scheduler.view_fpt_schedule`; managers require
`scheduler.manage_fpt_schedule`, which includes reading. Both policies require
an active user with role `STAFF` or `INSTRUCTOR`. Students cannot access these
actions even if they have either permission. Anonymous requests redirect to login.

POST accepts a JSON object or normal Django form data. Send the usual CSRF token.
Edits accept only changed fields and preserve omitted fields, including boolean
values. Explicitly send `is_active: false` to close a period. Unknown fields and
nested inputs are rejected. Omitted `is_active` on creation defaults to false.

Period creation fields: `start_date`, `end_date` (ISO dates), optional `is_active`.
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
