# UC-07 Sign in and open accessible projects

Supporting use case. It does not answer a pavement question, but every other use case depends on it.

## Actor
- Every user of the platform: pavement management engineer; airport pavement management staff; district/maintenance staff; client data administrator; client manager; project lead; Continuum consultant; Continuum administrator.

## Goal
Sign in and work only with the projects the user has been granted.

## Example request
"Sign in and open my projects."

## Data required
- The user's identity.
- The projects granted to the user and the user's permissions on each one (UC-08).

## Expected result
- Users sign in through the identity service, with multi-factor authentication: a platform account, their organization's own account (single sign-on, for clients that require it), or, for Continuum staff, their Google Workspace account.
- After sign-in, the project list shows only the projects granted to the user.
- A user without access to any project cannot sign in.
- Opening a project that was not granted is refused.
- Inside a granted project, the available actions match the user's permissions on that project (see the permissions table in README.md).

## Open items
- Which hosted identity service is used (ADR 2026-11-23-delegate-sign-in-to-an-identity-service).
