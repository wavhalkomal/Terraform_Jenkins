"""CloudLaunch Enterprise public product preview.

Safe by design: demo-only; no AWS, Jenkins, Terraform, or paid-resource calls.
The public app uses synthetic data and per-session request state.
"""
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

st.set_page_config(page_title="CloudLaunch Enterprise", page_icon="☁️", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container {padding-top:1.8rem;max-width:1480px}
[data-testid="stSidebar"] {background:#0f172a}
[data-testid="stSidebar"] * {color:#f8fafc}
.hero {background:linear-gradient(110deg,#0b1c37,#173a68);
padding:30px;border-radius:18px;color:white;margin-bottom:22px}
.hero h1{color:white;font-size:2.15rem;margin-bottom:5px}
.hero p{color:#b9d2ef;font-size:1.02rem}
.pill {background:#dbeafe;color:#1e40af;border-radius:8px;padding:4px 10px;
font-weight:700;font-size:.8rem}
</style>""", unsafe_allow_html=True)

if "requests" not in st.session_state:
    st.session_state.requests = [
        {"ID":"DEMO-101","Project":"Payments","Service":"EC2","Environment":"Development",
         "Size":"t3.micro","Status":"Provisioned (sample)","Owner":"Rahul","Created":"Sample"},
        {"ID":"DEMO-102","Project":"Payments","Service":"EC2","Environment":"Development",
         "Size":"t3.small","Status":"Duplicate blocked (sample)","Owner":"Priya","Created":"Sample"},
        {"ID":"DEMO-103","Project":"Analytics","Service":"EC2","Environment":"QA",
         "Size":"t3.micro","Status":"Approval pending (sample)","Owner":"Sam","Created":"Sample"},
    ]

st.sidebar.title("☁️ CloudLaunch")
st.sidebar.caption("ENTERPRISE PLATFORM • PRODUCT PREVIEW")
page = st.sidebar.radio("Workspace",
    ["Overview","Service Catalog","My Requests","Approvals","Infrastructure",
     "Pipelines","Cost & Governance","Product Architecture"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.info("🛡️ PUBLIC DEMO MODE\n\nNo cloud credentials, real servers, or billable deployments. Data is illustrative or local to your session.")
st.sidebar.caption("CloudLaunch • Built with Python, Streamlit, Terraform, Jenkins & AWS")

st.markdown("""<div class="hero"><span class="pill">PUBLIC PRODUCT PREVIEW</span>
<h1>CloudLaunch Enterprise</h1>
<p>One workspace to request, govern, deploy, and observe cloud infrastructure.</p>
</div>""", unsafe_allow_html=True)

if page == "Overview":
    st.subheader("Operations overview")
    a,b,c,d = st.columns(4)
    a.metric("Requests in this demo",len(st.session_state.requests))
    b.metric("Provisioned examples",sum("Provisioned" in r["Status"] for r in st.session_state.requests))
    c.metric("Duplicates prevented (examples)",sum("Duplicate" in r["Status"] for r in st.session_state.requests))
    d.metric("Live AWS spend","Not connected")
    st.info("Demo records below are synthetic. Historic Jenkins/AWS tests were previously verified separately; this site is not connected to those systems.")
    left,right = st.columns([1.6,1])
    with left:
        st.subheader("Request activity")
        st.dataframe(pd.DataFrame(st.session_state.requests),hide_index=True,use_container_width=True)
    with right:
        st.subheader("Platform capabilities")
        st.success("✔ Employee self-service catalog")
        st.success("✔ Duplicate-prevention design")
        st.success("✔ Approval and workflow preview")
        st.info("Live inventory, durable approvals, and production orchestration are planned enterprise integrations.")

elif page == "Service Catalog":
    st.subheader("Request infrastructure")
    st.caption("Submit a simulated request. Nothing is sent to AWS, GitHub, or Jenkins.")
    with st.form("new_request",clear_on_submit=True):
        c1,c2 = st.columns(2)
        name=c1.text_input("Employee name",placeholder="Your name")
        project=c2.text_input("Project / application",placeholder="payment-api")
        c3,c4,c5=st.columns(3)
        env=c3.selectbox("Environment",["Development","QA","Production"])
        size=c4.selectbox("Instance type",["t3.micro","t3.small","t3.medium"])
        service=c5.selectbox("Service",["EC2"],help="Additional infrastructure templates are on the roadmap.")
        purpose=st.text_area("Business justification",placeholder="Why is this infrastructure needed?")
        submitted=st.form_submit_button("Submit demo request",type="primary",use_container_width=True)
    if submitted:
        if not name.strip() or not project.strip() or not purpose.strip():
            st.error("Employee name, project, and justification are required.")
        else:
            duplicate=any(r["Project"].casefold()==project.strip().casefold()
                and r["Environment"]==env and r["Service"]==service
                and "Provisioned" in r["Status"] for r in st.session_state.requests)
            status="Potential duplicate — review required (demo)" if duplicate else "Approval pending (demo)"
            code="DEMO-"+uuid.uuid4().hex[:6].upper()
            st.session_state.requests.insert(0,{"ID":code,"Project":project.strip(),"Service":service,
                "Environment":env,"Size":size,"Status":status,"Owner":name.strip(),
                "Created":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")})
            st.success(f"{code} recorded for this browser session. Status: {status}")
            st.warning("The duplicate detection here is illustrative, not a substitute for the real AWS inventory and backend policy checks.")
    st.markdown("#### Planned service catalog")
    st.write("EC2 compute · S3 buckets · IAM requests · Managed databases · Container hosting · Network services")
    st.caption("Only the EC2 form is interactive in this preview, and all submissions remain simulated.")

elif page == "My Requests":
    st.subheader("Request center")
    st.dataframe(pd.DataFrame(st.session_state.requests),hide_index=True,use_container_width=True)
    st.caption("New demo submissions are stored only in your current Streamlit session and may disappear after a restart.")
    st.download_button("Export current demo requests (CSV)",
        pd.DataFrame(st.session_state.requests).to_csv(index=False), "cloudlaunch-demo-requests.csv","text/csv")

elif page == "Approvals":
    st.subheader("Approval workspace")
    st.warning("Preview only: this public site has no authenticated manager role. It cannot approve infrastructure.")
    pending=[r for r in st.session_state.requests if "pending" in r["Status"].lower() or "review" in r["Status"].lower()]
    st.dataframe(pd.DataFrame(pending) if pending else pd.DataFrame(columns=["ID","Project","Status"]),
                 hide_index=True,use_container_width=True)
    st.write("Enterprise version: employee → manager → platform engineer → policy check → Jenkins approval → Terraform.")

elif page == "Infrastructure":
    st.subheader("Infrastructure inventory")
    st.info("Live AWS inventory is intentionally disconnected. Previously created test EC2 instances were deleted to avoid charges.")
    st.metric("Live EC2 inventory","Not connected")
    st.metric("Last verified AWS sync","Not available")
    st.write("Enterprise edition will include live EC2 state, tags, owner, region, health, drift, and safe lifecycle actions.")

elif page == "Pipelines":
    st.subheader("Automation & deployment pipelines")
    st.success("Previously verified: GitHub merge → Jenkins dispatch → Python tests → AWS duplicate check.")
    st.code("cloudlaunch-dispatch → cloudlaunch-cd → duplicate policy → Terraform plan → approval → apply")
    st.info("This site cannot currently read local Jenkins build logs or trigger builds. Integration requires a secure backend accessible to the hosted app.")
    st.link_button("Open source repository","https://github.com/wavhalkomal/Terraform_Jenkins")

elif page == "Cost & Governance":
    st.subheader("Cloud cost & governance")
    st.metric("Live AWS charges","Not connected")
    st.info("No AWS Cost Explorer account access is configured on this public demo.")
    st.write("Planned controls: project budgets, cost estimates before approval, duplicate resource policies, spend alerts, expiring development instances and audit trails.")
    st.warning("Public demo submissions do not launch infrastructure or incur EC2 costs.")

else:
    st.subheader("Enterprise product architecture")
    st.code("""Streamlit frontend (public demo / employee portal)
            ↓ HTTPS + authentication
FastAPI backend (roles, API, audit policy)
            ↓
PostgreSQL + durable workflow queue
            ↓
Jenkins / GitHub / Terraform deployment workers
            ↓
AWS EC2 / S3 / IAM / CloudWatch / Cost Explorer
            ↖ live read-only status sync into portal""",language="text")
    st.markdown("**Available now:** tested Python/AWS duplicate-detection and Jenkins/Terraform automation.")
    st.markdown("**Next implementation phase:** authenticated APIs, persistent data, secure deployment triggers, real resource sync, complete audits, reliability controls.")
    st.link_button("View repository","https://github.com/wavhalkomal/Terraform_Jenkins")
