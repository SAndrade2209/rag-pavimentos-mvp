# UC-08 Manage project access

Supporting use case.

## Actor
- Client manager.
- Project lead.
- Continuum administrator.

[assumption] Scope of each actor:
- Client manager: all projects of their client.
- Project lead: their own project.
- Continuum administrator: sets up each client and its first client manager, and can grant access to any project.

## Goal
Give a person access to a project, set what they can do in it, and remove that access when it is no longer needed.

## Example request
- "Give this engineer View and Load permissions on project X."
- "Remove this person's access to project X."

Project X is a placeholder.

## Data required
- The person.
- The project.
- The permissions: View, Load, Correct and delete, Manage access (see the permissions table in README.md).

## Expected result
- The person can open the project, with only the actions their permissions allow (UC-07).
- Removing access stops the person from opening the project.
- [assumption] The PCI data the person loaded stay in the platform after their access is removed.
- [assumption] Each grant or removal records who made it and when.

## Open items
- Whether a project lead can give the Manage access permission to others.
- Whether access expires, for example when a consultant's work on a project ends.
