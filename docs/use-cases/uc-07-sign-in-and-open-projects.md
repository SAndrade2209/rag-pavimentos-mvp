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
- After sign-in, the project list shows only the projects granted to the user.
- A user without access to any project cannot sign in.
- Opening a project that was not granted is refused.
- Inside a granted project, the available actions match the user's permissions on that project (see the permissions table in README.md).

## Open items
- Sign-in method: platform accounts, or the agency's or airport's own accounts. In the second case, the organization's identity provider becomes an external system in C1.
