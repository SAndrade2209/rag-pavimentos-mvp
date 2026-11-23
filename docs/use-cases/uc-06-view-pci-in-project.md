# UC-06 View PCI data in a project

## Actor
- [assumption] Primary: pavement management engineer; airport pavement management staff; district/maintenance staff.
- [assumption] Secondary: Continuum consultant.

## Goal
See the current PCI of the sections in a project, and the PCI history of one section, without writing a question.

## Example request
- "Open the PCI data of this project."
- "Open section X."

This use case is navigation, not a question, so it gives example requests. Section X is a placeholder.

## Data required
- Section
- PCI
- Year

## Expected result
- Only projects the user has access to are shown (UC-07). Requires the View permission.
- Project data overview: a table of the project's sections with the latest PCI and the survey year of that PCI.
- Section view, opened from the overview:
  - PCI by survey year, as a chart. Years without a survey are marked as gaps, not filled.
  - Survey timeline: when each PCI survey of the section was done.
- The section view shows every survey year stored for the section on the network, including surveys loaded through other projects.

## Open items
- Dashboards beyond the project overview and the section view: not confirmed.
- How a section loaded through different projects is matched to the same network section (see UC-05).
