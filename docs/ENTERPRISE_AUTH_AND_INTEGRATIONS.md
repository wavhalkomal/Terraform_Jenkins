# CloudLaunch Enterprise — multi-tenant identity and integration blueprint

## Product promise

One CloudLaunch sign-in per user, connected to the user's own organization. Do **not** ask employees or public visitors to enter the platform owner's AWS IAM credentials, root keys, Jenkins administrator token, or personal GitHub token.

The public Streamlit Community Cloud application is a **read-only product showcase** until organization identity, a production backend, and durable policy enforcement are available. It must not provide a real provisioning path based on an unauthenticated form.

## Sign-in and organization onboarding

1. Organization administrator registers a tenant after authenticating with an OIDC identity provider (such as corporate Entra ID or Google Workspace).
2. Organization administrators verify the organization, configure eligible domains/SSO policies, and invite/approve members. Never assume all users sharing an email domain belong to a tenant without verification.
3. Each member signs in with OIDC Authorization Code + PKCE, validated state and nonce. The backend validates issuer, audience, signature, expiry and tenant membership.
4. Each authenticated session has an explicit organization ID and enforced role(s). Roles: employee, manager/reviewer, platform admin, security/auditor. Least privilege and separation of duties.
5. Every API operation revalidates the user's permissions and organization. A Streamlit widget or client-side hidden control is not an authorization boundary.

## Company integrations (configured by authorized organization admins)

### AWS

- Connect only the customer's AWS account(s) via a **customer-approved, narrowly scoped cross-account IAM role** with a unique external ID and role trust. Use STS AssumeRole for short-lived credentials. Do not store long-lived AWS IAM user keys in the Streamlit app.
- Separate read-only inventory role and restricted provisioning execution role. Bound the execution role by account, region, requestable templates, tags and limits; never permit unrestricted administrative access.
- Verify the connection using STS GetCallerIdentity and read-only Describe* API calls, with explicit permission and account-ID confirmation.
- Any write operation requires authenticated request, policy validation, duplicate/drift inspection, cost/quotas evaluation, approval and auditable provisioning worker execution.

### GitHub

- Prefer tenant-owned **GitHub App installation** with granular selected-repository permissions, not a shared platform owner's personal access token.
- Installation state must be linked to the authenticated organization using a CSRF-protected OAuth/app callback.
- Verify installation/repository access, then expose read-only workflow/PR/commit status before enabling narrowly scoped webhook-driven request dispatch.
- GitLab/Azure DevOps can be separate provider integrations with equivalent controls.

### Jenkins / CI servers

- Each company configures their Jenkins endpoint through admin-only onboarding. Verify certificate, permitted job scope, service-account permissions, connectivity and webhook authenticity.
- Do **not** publicly expose a local Jenkins controller at localhost:8080 or grant its admin token to Streamlit Community Cloud.
- Recommended: an authenticated outbound connector/agent or a private network service-to-service integration that only accepts signed, scoped requests and reports signed status events. Never permit arbitrary Groovy, shell commands, Jenkinsfile modifications, URL overrides, or unrestricted job dispatch from users.
- Report disconnected or unreachable status clearly; retry with durable queue and idempotency.

### Terraform

- Terraform remains an execution engine behind approved worker jobs. Maintain isolated backend state per organization/account/workload; never allow users to select arbitrary backend keys.
- Enforce plan policy (allowlisted infrastructure changes), human approval, re-check before apply, locking and full immutable audit records.

## Persistent services required

- Backend: FastAPI (or equivalent) for OIDC sessions, org membership, permissions, tenant integrations, requests, policy, activity and callback APIs.
- Database: PostgreSQL with tenant-scoped relational records, protected secrets references and durable transactional outbox.
- Workflow: durable queue with retries, timeout, idempotency keys and dead-letter handling.
- Secrets: managed KMS-backed secret storage. The database stores encrypted references, not public tokens.
- Monitoring: structured tenant-scoped logs, authorization decisions, webhook signature validation, audit records.
- Hosting: dedicated secure backend and worker environment. Streamlit Community Cloud may continue as marketing/showcase, but is not the production multi-tenant execution boundary.

## Gate before enabling live provisioning

- Authenticated, verified organization and employee membership
- Organization administrator-approved AWS and CI integration
- Restrict tenants to own accounts and repositories
- Least-privilege roles; no personal AWS/admin secrets
- Request validation and organization-scoped duplicate detection
- Explicit multi-stage approvals (prevent self-approval where required)
- Read-only plan with guardrails and price/quota ceilings
- Final duplicate check just before deployment
- Recorded artifact/signature, results and immutable audit event
- Reconciliation and safe destroy workflows to prevent drift/charges

## Implementation phases

1. GitHub Actions read-only connection and actual status (public API; no secrets).
2. Backend + PostgreSQL + identity, organization membership and RBAC.
3. Admin connection wizard: GitHub App, read-only AWS AssumeRole, Jenkins safe agent.
4. Durable requests, approvals, multi-tenancy and audit.
5. Read-only live AWS inventory, CI status and cost APIs.
6. Restricted apply/destroy workers and production reliability/security verification.

**Do not label a product fully integrated until each named provider connection is authenticated, verified, and tested end-to-end with tenant isolation.**
