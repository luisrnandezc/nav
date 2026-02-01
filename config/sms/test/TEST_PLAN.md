# SMS App – Test Plan

Focused on the most important flows: VHR lifecycle, risks, mitigation actions, and school status.

---

## 1. VHR creation and basic data

| # | What | Priority |
|---|------|----------|
| 1.1 | Create VoluntaryHazardReport with required fields (description, area, date, time) | High |
| 1.2 | Create Risk linked to a VHR (report, description, status, condition) | High |
| 1.3 | Create MitigationAction linked to a Risk (description, status, due_date, follow_date, responsible) | High |
| 1.4 | VHR with multiple risks and multiple mitigation actions per risk | Medium |

**Scope:** Model creation and relations. No forms/views.

---

## 2. VHR validity

| # | What | Priority |
|---|------|----------|
| 2.1 | Set VHR as valid (`is_valid=True`, `invalidity_reason` empty or None) | High |
| 2.2 | Set VHR as invalid (`is_valid=False`, `invalidity_reason` set) | High |
| 2.3 | Processing requires registered report; validity change blocked after processing (view-level; optional in first phase) | Low |

**Scope:** `is_valid` and `invalidity_reason` on VoluntaryHazardReport.

---

## 3. Mitigation actions: assignment and dates

| # | What | Priority |
|---|------|----------|
| 3.1 | Assign responsible (Staff/Instructor user) to MitigationAction | High |
| 3.2 | Set due_date and follow_date on MitigationAction | High |
| 3.3 | Default due_date 15 days from now, follow_date 7 days from now (model defaults) | Medium |

**Scope:** Model fields and defaults; assignment logic if in model/admin.

---

## 4. Registration and processing of VHR

| # | What | Priority |
|---|------|----------|
| 4.1 | Register VHR: set code (e.g. SMS-RVP-{id}) and `is_registered=True` | High |
| 4.2 | Process VHR: create risks and mitigation actions from ai_analysis_result; set `is_processed=True` | High |
| 4.3 | Processing only when `is_registered=True`; cannot process twice (view-level; optional in first phase) | Low |

**Scope:** `is_registered`, `is_processed`, code; creation of Risk and MitigationAction from analysis data (logic in view can be tested via integration test or mocked data).

---

## 5. Marking mitigation action as completed

| # | What | Priority |
|---|------|----------|
| 5.1 | Set MitigationAction.status to COMPLETED | High |
| 5.2 | Completing an action does not change risk condition if other actions for same risk are still PENDING | High |
| 5.3 | When all mitigation actions for a risk are COMPLETED, risk.condition becomes MITIGATED (view/signal or helper) | High |

**Scope:** Status update and downstream risk.condition update (tested via model + signal or view).

---

## 6. Risk status when all mitigation actions are completed

| # | What | Priority |
|---|------|----------|
| 6.1 | Risk.condition remains UNMITIGATED while any linked MitigationAction is not COMPLETED | High |
| 6.2 | Risk.condition becomes MITIGATED when every linked MitigationAction has status COMPLETED | High |
| 6.3 | If one action is reverted to PENDING (or new PENDING action added), risk.condition goes back to UNMITIGATED (if implemented) | Medium |

**Scope:** Risk.condition and its update when MMR statuses change (signals or view logic).

---

## 7. VHR status when all risks are mitigated

| # | What | Priority |
|---|------|----------|
| 7.1 | VoluntaryHazardReport.is_resolved is False while any risk has condition UNMITIGATED | High |
| 7.2 | VoluntaryHazardReport.is_resolved becomes True when all risks have condition MITIGATED | High |
| 7.3 | Signal (or equivalent) updates report.is_resolved when risk.condition or MitigationAction.status changes | High |

**Scope:** `is_resolved` and signal `check_and_update_report_resolved_status`.

---

## 8. SMS school status (tolerable / acceptable unmitigated risk)

| # | What | Priority |
|---|------|----------|
| 8.1 | sms_school_status = CRÍTICO when any unmitigated risk has status INTOLERABLE | High |
| 8.2 | sms_school_status = CRÍTICO when unmitigated TOLERABLE count > 4 | High |
| 8.3 | sms_school_status = PRECAUCIÓN when unmitigated TOLERABLE count > 0 and ≤ 4 (and no intolerable) | High |
| 8.4 | sms_school_status = SEGURO when no unmitigated INTOLERABLE/TOLERABLE (only ACCEPTABLE or none) | High |
| 8.5 | sms_school_status = NO CALCULADO when no unmitigated risks or logic not run (if applicable) | Medium |

**Scope:** Logic that computes sms_school_status from unmitigated risks (view context or extracted helper).

---

## Out of scope (for now)

- AI analysis flow and email notifications
- PDF generation and download
- Full form validation and permission checks (can be added later)
- UI / Selenium tests

---

## Implementation notes

- **Models:** Test creation and relations with factories (VHR, Risk, MitigationAction).
- **Signals:** Test that completing all MMRs for a risk sets risk.condition = MITIGATED, and that when all risks are MITIGATED, report.is_resolved = True.
- **School status:** Test by creating unmitigated risks with different statuses and asserting the computed sms_school_status (via view context or a small helper).
- Prefer simple, fast unit tests; add a few integration tests only where necessary (e.g. processing a VHR and then checking risks/MMRs/resolved/status).
