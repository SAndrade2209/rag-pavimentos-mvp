# UC-09 Correct or delete PCI data

Supporting use case.

## Actor
- Any user with the Correct and delete permission on the project (UC-08).

## Goal
Fix a wrong PCI value, or remove records loaded by mistake, without losing the record of what was there before.

## Example request
- "Change the 2024 PCI of section X from 85 to 58; the digits were swapped when the data were entered."
- "Remove the rows from yesterday's load; the file belonged to another airport."

The values and section X are examples.

## Data required
- Section, year and PCI of the record to correct or delete.
- The reason for the change.

## Expected result
- From then on, answers (UC-01 to UC-04) and views (UC-06) use the corrected value.
- The old value, or the deleted record, is hidden from views and answers but kept, with who made the change, when and why.
- [assumption] The change history of a section can be viewed.

## Open items
- Who can see the change history.
- Whether a deleted record can be restored.
