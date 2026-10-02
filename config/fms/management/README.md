# Local FMS demo data

From the `config` directory, run:

```sh
python manage.py migrate
python manage.py seed_fms_demo
```

The command requires `DEBUG=True` and `IS_PRODUCTION=false`. It performs database
writes only; it does not send email or run AURA analysis. A temporary dummy mail
backend discards transaction-signal notifications, then restores the normal mail
settings on success or failure. All writes are atomic.
This suppression applies to the command only; subsequent UI actions use the
application's configured email backend. Use a local mail backend for UI testing.

## Demo logins

The password for every demo account is **`navdemo26%`**. These credentials are
only for local development. Re-running the command without `--reset` preserves
existing records and passwords.

| Username | National ID | Name | Role | What to check |
| --- | ---: | --- | --- | --- |
| `demo_fms_student` | `99001001` | Ana Actividad | Student | 28 PPA flights, more than 25 movements, filters/pagination, positive balance, confirmed credit, pending credit, materials debit, credit adjustment, and immediate/missing/later fuel |
| `demo_fms_advanced` | `99001002` | Luis Avanzado | Student | Four PCA flights, $95/h student rate, 120 carried-over hours outside NAV |
| `demo_fms_debt` | `99001003` | Eva Saldo negativo | Student | Two HVI flights, partial payment, negative balance, 100 carried-over hours outside NAV |
| `demo_fms_empty` | `99001004` | Leo Sin actividad | Student | Empty logbook, zero balance and hours, unavailable averages |
| `demo_fms_instructor` | `99001005` | Carlos Instructor | Instructor | Instructor logbook, flight evaluations and entry forms |
| `demo_fms_staff` | `99001006` | Sofia Administración | Staff | FMS dashboard, student statistics, transactions, pending-payment confirmation and missing-fuel entry; includes the required transaction permissions |

For the staff preview, log in as `demo_fms_staff` and open **Estadísticas y
movimientos**. For student-facing flight pages, use one of the student accounts
and open **Bitácora**. The staff account is not a superuser.

## Repeatability and reset

```sh
python manage.py seed_fms_demo --reset
python manage.py seed_fms_demo --reset --as-of 2026-09-24
```

The default scenario end date is today. `--as-of` fixes all relative flight and
payment dates for repeatable screenshots. Reset recreates marked activity and
restores the demo passwords, balances, rates and hours. Accounts and aircraft
retain their IDs. It never deletes non-demo users or takes over a matching name.

Reset deliberately refuses to proceed if manual/unmarked FMS activity or
transactions reference the demo accounts/aircraft, or if seeded flights have AURA
reviews. This prevents erasing UI experiments or changing unrelated balances.
Review those records before rebuilding; there is no force-delete option.

Ownership is marked with the `FMS demo dataset v1` group and
`[seed_fms_demo:v1]` notes/comments. Do not remove these markers. Missing/modified
ownership records cause the command to stop instead of guessing what it owns.

## Accounting and scope

Flight records go through the same validated forms used by the UI, including
hour totals, saved rates and automatic debits. Transactions use their normal
balance updates. Later fuel uses the shared `record_late_fuel()` operation used
by the staff fuel page. Student balances reconcile to the applied movement list;
pending payments do not contribute. Carried-over hours are explicit starting
profile values, not invented paid NAV flights.

Aircraft `DEMO-FMS-01` and `DEMO-FMS-02` are separate from the real fleet.
Both use $3.11 per liter, including recreated flight and fuel charges. Overall
student statistics include them. Existing views hardcoded to `YV204E`/`YV206E`
(including per-aircraft student sections and instructor/fleet statistics) do not
gain those aircraft's demo activity. This command does not modify real aircraft
to fill those sections. It seeds school flight evaluations and their accounting,
not simulator sessions, external evaluations, scheduling or academic enrollments.
Required course types are created if missing and retained on reset as shared
reference data; existing course types are never changed.

## Tests

```sh
python manage.py test fms.test.test_seed_fms_demo transactions --noinput
```
