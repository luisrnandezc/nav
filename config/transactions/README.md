# Student balance and statistics

Students can open `/transactions/student/` from the dashboard to see only their
own balance, total hours, NAV hours, weighted fuel/cost averages, and paginated
history. The student view has no account search or selector. Staff using the same
page can search and select a student only when they have the
`accounts.can_manage_transactions` permission. Filters only affect the history.

## Accounting sources

Manual movements come from StudentTransaction. Confirmed manual transactions
affect the balance, while all manual transactions appear in the history; neither
credits nor debits contribute to flight cost statistics, even when their category
is `VUELO`. The summary banner and complete statistics page both use
`fms.statistics.calculate_student_stats()`: it aggregates current hours and fuel
directly from the three school evaluation types, applies each evaluation's saved
hour and fuel rates, and includes every school aircraft. Later price changes do
not rewrite historical costs. External flights and simulator sessions are excluded.

Later fuel transactions retain a nullable foreign key to their evaluation, liters,
unit price, charged amount, and a generated description with flight date, aircraft,
hours, instructor, and reference. Staff may append observations. Linked fuel is
excluded from the original flight charge and shown as a separate dated debit.
Changing fuel or hourmeters later through the flight admin creates confirmed,
flight-linked correction movements. Reductions create credits; increases create
debits. The correction uses the rates saved on the flight, and the flight update,
hour totals, transaction, and balance change commit atomically. Applied movements
cannot be changed or deleted through the transaction admin.
The transaction history separately reconstructs each automatic debit using its
saved historical rates. This preserves the accounting explanation without using
ledger reconstruction as the source for current operational statistics.

## Migration and historical limits

Run `python manage.py migrate` from `config` before using the new tile.
Migration 0012 adds fuel references and snapshots. Migration 0013 links legacy
fuel notes only when student, aircraft, instructor, liters, and date identify one
candidate flight and only one transaction matches it. It does not change balances.
Ambiguous or missing flight references remain unlinked and generate a warning.
They appear in the history but do not contribute to the USD/hour average.
Migration 0014 adds the correction type and flight-hour snapshot fields and labels
existing fuel snapshots as later-fuel movements. It does not change balances.

The history reflects currently retained flight and transaction records. Existing
data does not provide an immutable audit of deleted records, prior edits, starting
balances, or confirmation reversals. This implementation does not invent such
events or historical running balances. Exact reconciliation of older accounts
requires reviewing those records; a permanent event ledger is separate work.

The detailed statistics template retains its existing two named aircraft sections;
overall totals and overview averages include all school aircraft.

## Reading the activity code

Start with `student_activity()` at the bottom of `student_activity.py`. It is the
entry point used by both views and coordinates the helpers in this order:

1. Load the student's transactions and call `group_fuel_transactions_by_flight()`.
   `get_fuel_flight_key()` identifies a flight by both its table kind and ID.
2. Call `summarize_student_flights()`. It loads flights through
   `iter_student_flights()`, calculates each charge with
   `calculate_flight_charges()`, and formats it with `build_flight_movement()`.
3. Pass the flight totals to `build_detailed_statistics()` for totals and
   averages. Manual movements never enter this calculation.
4. Use `is_fuel_transaction()` to flag unresolved fuel and
   `build_transaction_movement()` to format manual movements. Merge those rows
   with the flight rows and sort newest first.

`FlightCharges` names the amounts passed between calculation and presentation:
original hours and fuel, the combined original debit, and signed confirmed fuel
and flight-time adjustments. The view handles filters and pagination after this
module returns its result. All helpers are read-only.

## Verification

`python manage.py test transactions dashboard fms.test.test_flight_evaluation_rates --noinput`

Covers student isolation, pending credits, date/filter/pagination handling, saved
rates, delayed fuel linkage and duplicate submission, atomic rollback, invalid
fuel input, legacy matching, and existing flight accounting behavior.
