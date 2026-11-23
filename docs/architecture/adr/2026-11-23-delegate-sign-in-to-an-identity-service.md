# Delegate sign-in to an identity service

- Date: 2026-11-23
- Status: Accepted

## Context

- UC-07: users sign in and see only the projects granted to them; a user without access to any project cannot enter. UC-08: managers grant and remove access per project.
- Two things are often mixed up:
  - **Authentication:** proving who the user is. This ADR covers it.
  - **Authorization:** what that user may do (projects and permissions, UC-07 and UC-08). It stays in the platform and is not decided here.
- Facts:
  - Some clients may require their staff to sign in with their own organization's accounts (single sign-on); others may accept accounts created in the platform. Both cases have to be supported.
  - Continuum staff (consultants and administrators) use Google Workspace accounts.
  - Multi-factor authentication (MFA) is required for every user.
- Constraints (CLAUDE.md): data stay in the US; the platform runs on any major cloud provider.
- Quality attributes involved (quality-attributes.md): security (high), deployability and simplicity (high), usability (medium), interoperability (medium).

Options considered:

1. **Build sign-in in the API application.** We write and maintain password storage, MFA and each single sign-on integration, using libraries.
2. **Self-hosted open-source identity server** (for example, Keycloak), run as a new container.
3. **Hosted identity service** from a company independent of the cloud host (for example, Auth0). The identity services of cloud providers themselves are excluded, because they tie the platform to one provider.
4. **Google sign-in for everyone.** Excluded: client staff do not have Google accounts from Continuum.

## Decision

- Sign-in is delegated to an identity component through the OpenID Connect standard. The API application accepts only signed sign-in tokens from that component and stores no passwords.
- The identity component provides:
  - platform accounts, with MFA required;
  - single sign-on with a client's own identity provider, set up per client when that client requires it;
  - Google Workspace sign-in for Continuum staff.
- The MVP starts with option 3, a hosted identity service, provided the chosen service keeps user data in the US and its price fits the budget. If no service meets both, option 2.
- Options 2 and 3 both use OpenID Connect, so moving from one to the other later changes configuration, not the platform's code.
- Authorization stays in the platform. After sign-in, the API application checks the user's projects and permissions (UC-07, UC-08), including the rule that a user without any project cannot enter.
- The specific service is chosen after checking US data location, MFA and single sign-on support, and price.

## Attributes gained

- **Security (high):** the platform stores no passwords. MFA and single sign-on come from a component built for that purpose. For clients with single sign-on, and for Continuum staff, access ends automatically when a person leaves their organization.
- **Deployability and simplicity (high):** no sign-in code to write and maintain. With a hosted service, no new container.
- **Usability (medium):** client staff with single sign-on use their work account; Continuum staff use their Google account.
- **Interoperability (medium):** OpenID Connect and the single sign-on standards are what client identity providers already support.

## Attributes sacrificed

- **Deployability and simplicity (high), partly:** one external service to configure, and a single sign-on setup with each client's IT department that requires it.
- **Security (high), partly:** user names and email addresses are kept by a third party. Mitigated by the US data location requirement and by keeping all project data and permissions in the platform.

## Consequences

- C1: new external systems: the identity service, client identity providers (for clients with single sign-on), and Continuum's Google Workspace. If option 2 is used instead, the identity server becomes a container in C2.
- UC-07: the open item on the sign-in method is resolved.
- For users who sign in with their organization's account, MFA is enforced by that organization's identity provider. Whether each client's provider requires it is confirmed per client.
- Continuum's Google Workspace must require two-step verification for staff who use the platform.
- The hosted service has a subscription price. The amount is not known yet and is part of choosing the service.
- Moving between hosted and self-hosted later requires migrating user accounts; users with platform accounts may need to reset their passwords.
- Open item: which hosted identity service.
