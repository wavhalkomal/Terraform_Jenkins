# CloudLaunch Enterprise • Public Product Preview

This is a safe, publicly shareable **Streamlit product preview** added to the existing CloudLaunch repository. It is **not yet an enterprise production system**. Request records are synthetic or stored per browser session. There are **no AWS, Terraform or Jenkins execution paths** in the public app.

## Deploy for free to Streamlit Community Cloud

1. Merge the product-preview PR after checks pass.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app → Yup, I have an app**.
4. Repository: `wavhalkomal/Terraform_Jenkins`
5. Branch: `main`
6. Main file path: `streamlit_app.py`
7. Optional public subdomain: `cloudlaunch-enterprise` (only if available).
8. Deploy and wait for a public `https://....streamlit.app` URL.
9. In your app select **Share → Copy link**.

Dependencies for this entrypoint are in the root `requirements.txt`.

### Local run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Security boundary

- **Never** configure AWS Administrator credentials or expose Jenkins API tokens in the public Community Cloud app.
- The hosted Streamlit process cannot directly access Jenkins on `localhost:8080` of your Mac.
- Production actions require authenticated backend APIs, scoped cloud roles, durable DB/workflow queue, and explicit approvals.
- This preview intentionally cannot create billable AWS resources.
- Streamlit session state is not a persistent database.

## Enterprise roadmap

1. FastAPI and PostgreSQL backend with durable requests and audit events.
2. Company SSO and role-based authorization (employees, managers, platform admins).
3. Back-end duplicate inventory checks and cost/policy guardrails.
4. Authenticated Jenkins orchestration with safe retry and callback events.
5. Live AWS inventory, logs, monitoring and cost telemetry.
6. Hardened deployment outside Community Cloud for enterprise customers.

## Existing deployment automation

Existing Jenkinsfiles, request JSONs, Python tests and Terraform infrastructure code remain untouched. Do not merge request files just to test this public preview: `cloudlaunch-dispatch` watches new `requests/*.json` paths and can trigger real provisioning.
