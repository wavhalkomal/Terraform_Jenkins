"""CloudLaunch Enterprise — safe white-theme showcase, no live cloud operations."""
import uuid
import html
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from cloudlaunch_portal.github_status import fetch_workflows
from cloudlaunch_portal.repository_requests import fetch_request_files

@st.cache_data(ttl=90, show_spinner=False)
def github_status():
 return fetch_workflows()

@st.cache_data(ttl=120, show_spinner=False)
def repository_requests():
 return fetch_request_files()

st.set_page_config(page_title="CloudLaunch Enterprise",page_icon="☁️",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
html,body,div,span,p,label,button,input,textarea,select,table,td,th,.stApp{font-family:'Times New Roman',Times,serif!important;letter-spacing:normal!important}
.stApp{background:#f6f8fc;color:#182941;font-family:'Times New Roman',Times,serif}
.block-container{max-width:1600px;padding:1.5rem 2rem 3rem}
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e5ebf3}
[data-testid="stSidebar"] *{color:#22334b}
[data-testid="stHeader"]{background:#f6f8fc}
h1,h2,h3{font-family:'Times New Roman',Times,serif,sans-serif!important;letter-spacing:normal!important;color:#162743}
[data-testid="stMetric"]{border:1px solid #e4eaf2;border-radius:16px;background:#fff;padding:17px 21px;min-height:125px;box-shadow:0 6px 22px #13284a05}
[data-testid="stMetricLabel"]{color:#64748b}
[data-testid="stMetricValue"]{font-family:'Times New Roman',Times,serif;font-weight:800;color:#162743}
[data-testid="stDataFrame"]{border:1px solid #e4eaf2;border-radius:12px;overflow:hidden}
[data-testid="stForm"]{background:#fff;border:1px solid #e4eaf2;border-radius:16px;padding:24px}
.stButton>button[kind=primary],div[data-testid="stFormSubmitButton"] button[kind=primary]{background:#2563eb!important;color:#fff!important;border:1px solid #2563eb!important;border-radius:10px!important;font-weight:700}
.stButton button{border-radius:10px;font-weight:650}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:#e4eaf2!important;border-radius:16px!important;background:white}
.brand{display:flex;align-items:center;gap:10px;font-family:'Times New Roman',Times,serif;font-weight:800;font-size:1.25rem;color:#162743;margin:12px 0 3px}
.brand-logo{display:inline-grid;place-items:center;width:39px;height:39px;border-radius:12px;color:#fff;background:#2563eb}
.small{font-size:.75rem;color:#8895a9;letter-spacing:.08em;text-transform:uppercase;font-weight:800}
.topbar{border:1px solid #e4eaf2;background:white;border-radius:14px;padding:15px 20px;display:flex;justify-content:space-between;align-items:center;margin-bottom:23px;font-size:.83rem;color:#697890}
.mode{color:#225cba;background:#eef5ff;padding:7px 11px;border-radius:20px;font-weight:800}
.eyebrow{color:#366bc2;font-size:.75rem;letter-spacing:.12em;font-weight:800;text-transform:uppercase}
.heading{font-family:'Times New Roman',Times,serif;font-size:2rem;font-weight:800;letter-spacing:normal;color:#172941;margin:7px 0}
.subheading{color:#71809a;font-size:.95rem;margin-bottom:24px}
.hero{background:linear-gradient(115deg,#edf5ff,#fff 68%,#e5f0ff);border:1px solid #dae7fb;padding:30px;border-radius:19px;margin-bottom:20px}
.hero h1{font-size:2rem!important;font-weight:800;margin:7px 0 10px}
.hero p{color:#667891;max-width:750px}
.section{display:flex;justify-content:space-between;align-items:center;margin:25px 0 13px}
.section strong{font-family:'Times New Roman',Times,serif;font-size:1.08rem;color:#192b46}
.section span{color:#8997a9;font-size:.78rem}
.tile{background:white;border:1px solid #e4eaf2;border-radius:16px;padding:22px;margin-bottom:15px;min-height:177px}
.tile h3{font-size:1rem!important;margin:10px 0}
.tile p{font-size:.83rem;color:#748198;line-height:1.6}
.iconbox{width:43px;height:43px;border-radius:13px;background:#eaf2ff;display:grid;place-items:center;font-size:22px}
.chip{background:#eaf3ff;color:#2563eb;font-size:.72rem;font-weight:800;padding:5px 9px;border-radius:8px}
.workflow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:20px 0}
.workflow span{background:#eff5ff;border:1px solid #dce9ff;padding:11px;border-radius:10px;color:#285db3;font-weight:700;font-size:.8rem}
.workflow b{color:#a4b2c8}
.note{background:#f1f6ff;border:1px solid #ddeaff;color:#506c9a;padding:15px;border-radius:13px;font-size:.8rem}

/* CloudLaunch brand motion: purely decorative; honors reduced motion. */
.hero{position:relative;overflow:hidden;isolation:isolate;min-height:210px}
.hero::before{content:"";position:absolute;z-index:-1;inset:0 0 0 52%;
background-image:radial-gradient(circle,#3b82f6 1.8px,transparent 2.7px),
repeating-linear-gradient(30deg,transparent 0 49px,rgba(50,110,205,.1) 50px,transparent 51px),
repeating-linear-gradient(150deg,transparent 0 59px,rgba(50,110,205,.07) 60px,transparent 61px);
background-size:53px 53px,100px 100px,110px 110px;opacity:.47;animation:network-drift 24s linear infinite}
.hero::after{content:"";position:absolute;z-index:-1;right:4%;top:-80px;width:360px;height:360px;
border:1px solid #bfdbfe;border-radius:50%;box-shadow:0 0 0 40px #dbeafe22,0 0 0 88px #eff6ff99;
background:radial-gradient(circle at 45% 46%,#93c5fd44,transparent 61%)}
@keyframes network-drift{to{background-position:106px 53px,90px 0,-110px 30px}}
@media(prefers-reduced-motion:reduce){.hero::before{animation:none}}
[data-testid="stSidebar"] .stRadio label{font-size:1rem}
</style>""",unsafe_allow_html=True)

if "requests" not in st.session_state:
 st.session_state.requests=[
 {"ID":"CL-2401","Project":"Payments Platform","Owner":"Rahul","Service":"EC2","Environment":"Development","Size":"t3.micro","Status":"Provisioned · sample","Created":"Oct 16"},
 {"ID":"CL-2402","Project":"Payments Platform","Owner":"Priya","Service":"EC2","Environment":"Development","Size":"t3.small","Status":"Duplicate blocked · sample","Created":"Oct 17"},
 {"ID":"CL-2403","Project":"Analytics Workspace","Owner":"Sam","Service":"S3","Environment":"QA","Size":"Standard","Status":"Awaiting approval · sample","Created":"Oct 17"},
 {"ID":"CL-2404","Project":"Digital Experience","Owner":"Alex","Service":"EC2","Environment":"Production","Size":"t3.medium","Status":"Policy review · sample","Created":"Oct 18"},
 {"ID":"CL-2405","Project":"Internal Tools","Owner":"Jamie","Service":"S3","Environment":"Development","Size":"Standard","Status":"Provisioned · sample","Created":"Oct 18"}]
if "decisions" not in st.session_state:st.session_state.decisions=[]

def section(a,b=""):
 st.markdown(f'<div class="section"><strong>{html.escape(a)}</strong><span>{html.escape(b)}</span></div>',unsafe_allow_html=True)
def heading(a,b,c="CLOUD OPERATIONS"):
 st.markdown(f'<div class="eyebrow">{html.escape(c)}</div><div class="heading">{html.escape(a)}</div><div class="subheading">{html.escape(b)}</div>',unsafe_allow_html=True)
def frame(rows):
 return pd.DataFrame(rows,columns=["ID","Project","Owner","Service","Environment","Size","Status","Created"])
def chart(kind):
 fig=go.Figure()
 if kind=="cost":
  d={"Compute":[340,390,410,495,470,520],"Storage":[85,91,108,104,120,135],"Network":[45,52,58,69,64,80]}
  for name,color in zip(d,["#2563eb","#7bacee","#c6dbff"]):fig.add_bar(x=["May","Jun","Jul","Aug","Sep","Oct"],y=d[name],name=name,marker_color=color)
  fig.update_layout(barmode="stack",legend=dict(orientation="h",y=1.2,x=0))
 else:
  fig.add_scatter(x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],y=[12,17,15,22,19,27,24],mode="lines+markers",line=dict(color="#2563eb",width=3,shape="spline"),fill="tozeroy",fillcolor="rgba(37,99,235,.08)")
 fig.update_layout(height=282,margin=dict(l=8,r=10,t=10,b=12),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#71819c"),xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#eef2f7"),showlegend=kind=="cost")
 return fig

with st.sidebar:
 st.markdown('<div class="brand"><span class="brand-logo">C</span>CloudLaunch</div><div class="small">Enterprise Cloud Platform</div>',unsafe_allow_html=True)
 st.write("")
 pages=["Overview","Service Catalog","Requests","Approvals","Infrastructure","Deployments","Cost & Governance","Integrations & Access","Architecture"]
 labels=["▦  Overview","⊞  Service Catalog","▤  Requests","✓  Approvals","◈  Infrastructure","⌁  Deployments","◉  Cost & Governance","⚙  Integrations & Access","◇  Architecture"]
 choice=st.radio("Navigation",list(range(len(pages))),format_func=lambda i:labels[i],label_visibility="collapsed")
 page=pages[choice]
 st.divider()
 st.markdown('<div class="note"><b>CLOUDLAUNCH PLATFORM STATUS</b><p style="margin-bottom:0">AWS infrastructure provisioning, Jenkins CI/CD automation, and duplicate prevention were implemented and tested with real AWS. Live infrastructure monitoring and deployment controls are not yet connected to this web portal. Sample cost charts and inventory are illustrative.</p></div>',unsafe_allow_html=True)
 st.write("")
 st.link_button("↗ GitHub source","https://github.com/wavhalkomal/Terraform_Jenkins",use_container_width=True)
st.markdown(f'<div class="topbar"><span>Workspace &nbsp; / &nbsp; <b>{html.escape(page)}</b></span><span class="mode">GitHub public API · AWS/Jenkins connection pending</span></div>',unsafe_allow_html=True)

if page=="Overview":
 st.markdown('<div class="hero"><div class="eyebrow">ENTERPRISE CLOUD PLATFORM</div><h1 style="font-size:3.2rem!important;margin:9px 0 4px">CloudLaunch</h1><p style="font-size:1.25rem;color:#223b64">Secure cloud infrastructure automation, approvals &amp; governance</p><p>Bring infrastructure requests, deployment policies, CI/CD visibility and operational control together in one platform.</p></div>',unsafe_allow_html=True)
 gh=github_status()
 real=repository_requests()
 a,b,c,d=st.columns(4)
 a.metric("Repository requests",len(real["rows"]) if real["connected"] else "Unavailable")
 b.metric("Verified EC2 creation tests",1,"Historical")
 c.metric("Verified duplicate blocks",2,"Historical")
 d.metric("GitHub Actions API","Connected" if gh["connected"] else "Unavailable")
 st.caption("The request table is sourced from actual GitHub JSON files. Provisioning and duplicate outcomes refer to previously verified Jenkins tests; the EC2 test instances were subsequently deleted.")
 section("Infrastructure requests","Real source files · historical deployment outcomes")
 if real["connected"]:
  st.dataframe(pd.DataFrame(real["rows"]),hide_index=True,use_container_width=True)
 else:
  st.warning(real["error"] or "GitHub request files unavailable")
 section("Platform integrations","Verified credentials and runtime access are separate checks")
 i1,i2,i3=st.columns(3)
 with i1:
  with st.container(border=True):
   st.markdown("**GitHub Actions**")
   st.write("API reachable" if gh["connected"] else "API unavailable")
   st.caption("Live read-only repository workflow telemetry")
 with i2:
  with st.container(border=True):
   st.markdown("**AWS**")
   st.write("Portal connection not configured")
   st.caption("Real EC2 deployment tested earlier via Jenkins")
 with i3:
  with st.container(border=True):
   st.markdown("**Jenkins**")
   st.write("Portal connection not configured")
   st.caption("Local Jenkins on Mac; tested separately")
 section("Latest GitHub Actions","Actual workflow runs · refreshes approximately every 90 seconds")
 if gh["connected"] and gh["runs"]:
  st.dataframe(pd.DataFrame(gh["runs"][:6]),hide_index=True,use_container_width=True,
     column_config={"Run URL":st.column_config.LinkColumn("Open run")})
 elif gh["connected"]:
  st.info("No GitHub workflow runs returned.")
 else:
  st.warning(gh["error"] or "GitHub API unavailable")
 st.caption("Organization SSO, cross-account AWS access and managed Jenkins connectors must be verified before anyone can provision infrastructure through this hosted website.")

elif page=="Service Catalog":
 heading("Infrastructure service catalog","Request standardized cloud services from one managed workspace.","SELF-SERVICE INFRASTRUCTURE")
 section("Request cloud compute","Website request form · no direct AWS creation")
 with st.form("request_form",clear_on_submit=True):
  a,b=st.columns(2)
  user=a.text_input("Employee name")
  project=b.text_input("Project / application")
  a,b,c=st.columns(3)
  env=a.selectbox("Environment",["Development","QA","Production"])
  size=b.selectbox("EC2 instance type",["t3.micro","t3.small","t3.medium"])
  region=c.selectbox("AWS region (demo)",["us-east-1","us-east-2","us-west-2"])
  purpose=st.text_area("Business justification")
  send=st.form_submit_button("Submit request →",type="primary",use_container_width=True)
 if send:
  if not all([user.strip(),project.strip(),purpose.strip()]):st.error("Complete the name, project and justification.")
  else:
   duplicate=any(r["Project"].casefold()==project.strip().casefold() and r["Environment"]==env and "Provisioned" in r["Status"] for r in st.session_state.requests)
   status="Duplicate review · demo" if duplicate else "Awaiting approval · demo"
   rid="CL-"+uuid.uuid4().hex[:6].upper()
   st.session_state.requests.insert(0,{"ID":rid,"Project":project.strip(),"Owner":user.strip(),"Service":"EC2","Environment":env,"Size":size,"Status":status,"Created":datetime.now(timezone.utc).strftime("%b %d")})
   st.success(f"{rid} submitted to this browser session; status: {status}. No server was created in {region}.")

 section("Explore available services","Future services · not yet implemented")
 services=[("☁","Cloud compute","Provision EC2 virtual machines with governed request flows.","REQUEST FORM"),("▤","Object storage","Encrypted S3 storage with lifecycle and retention controls.","COMING SOON"),("◉","Managed databases","Standardized database delivery and compliance controls.","COMING SOON"),("⬡","Container platforms","Scale containerized services with automated provisioning.","COMING SOON"),("◇","Networking","Managed VPC, routing and connectivity requests.","COMING SOON"),("♧","Identity & access","Auditable, least-privilege identity requests.","COMING SOON")]
 cols=st.columns(3)
 for i,(ic,name,desc,state) in enumerate(services):
  with cols[i%3]:
   st.markdown(f'<div class="tile"><div class="iconbox">{ic}</div><h3>{name}</h3><p>{desc}</p><span class="chip">{state}</span></div>',unsafe_allow_html=True)


elif page=="Requests":
 heading("Request management","Search, filter and export the complete demo request lifecycle.","WORKFLOW CENTER")
 a,b,c=st.columns(3)
 a.metric("Total requests",len(st.session_state.requests))
 b.metric("Pending review",sum("approval" in r["Status"] or "review" in r["Status"] for r in st.session_state.requests))
 c.metric("Blocked duplicates",sum("Duplicate" in r["Status"] for r in st.session_state.requests))
 section("Request register","Current visitor session")
 a,b=st.columns([2,1])
 query=a.text_input("Search requests",placeholder="Project, owner, request ID")
 status=b.selectbox("Status",["All statuses"]+sorted(set(r["Status"] for r in st.session_state.requests)))
 shown=[r for r in st.session_state.requests if (not query or query.casefold() in " ".join(map(str,r.values())).casefold()) and (status=="All statuses" or r["Status"]==status)]
 st.dataframe(frame(shown),hide_index=True,use_container_width=True)
 st.download_button("↓ Export filtered CSV",frame(shown).to_csv(index=False),"cloudlaunch-requests-demo.csv","text/csv")

elif page=="Approvals":
 heading("Approval operations","Review access and compute requests through explicit governance checkpoints.","POLICY AND REVIEW")
 st.info("Simulated decisions only. No authenticated reviewer identity and no real infrastructure approval.")
 pending=[r for r in st.session_state.requests if "approval" in r["Status"] or "review" in r["Status"]]
 a,b,c=st.columns(3)
 a.metric("Pending demo reviews",len(pending))
 b.metric("Policy escalations",sum("review" in r["Status"] for r in pending))
 c.metric("Demo decisions",len(st.session_state.decisions))
 section("Review queue")
 st.dataframe(frame(pending),hide_index=True,use_container_width=True)
 if pending:
  with st.container(border=True):
   opts={r["ID"]+" · "+r["Project"]:r for r in pending}
   target=st.selectbox("Select request",list(opts))
   note=st.text_input("Review note")
   a,b=st.columns(2)
   if a.button("Approve in demo",type="primary",use_container_width=True):
    opts[target]["Status"]="Approved in demo";st.session_state.decisions.append({"Request":opts[target]["ID"],"Decision":"Approved demo","Note":note});st.rerun()
   if b.button("Reject in demo",use_container_width=True):
    opts[target]["Status"]="Rejected in demo";st.session_state.decisions.append({"Request":opts[target]["ID"],"Decision":"Rejected demo","Note":note});st.rerun()
 if st.session_state.decisions:
  section("Session decision log");st.dataframe(pd.DataFrame(st.session_state.decisions),hide_index=True,use_container_width=True)

elif page=="Infrastructure":
 heading("Infrastructure explorer","Regional asset tracking and application ownership, ready for secure AWS integration.","CLOUD INVENTORY")
 st.info("Sample resources below are fictional. Your real test EC2 instances were deleted; this app has no AWS inventory connection.")
 a,b,c,d=st.columns(4)
 a.metric("Sample assets",6);b.metric("Sample regions",3);c.metric("Sample teams",4);d.metric("AWS inventory feed","Not connected")
 section("Asset inventory","Example records only")
 assets=pd.DataFrame([
 ["payments-api-dev","EC2","us-east-1","Development","Running · sample","Payments"],
 ["analytics-worker","EC2","us-east-2","QA","Running · sample","Analytics"],
 ["customer-web-prod","EC2","us-east-1","Production","Running · sample","Digital"],
 ["batch-processor","EC2","us-west-2","Development","Stopped · sample","Finance"],
 ["payments-artifacts","S3","us-east-1","Development","Configured · sample","Payments"],
 ["analytics-storage","S3","us-east-2","Production","Configured · sample","Analytics"]],
 columns=["Asset","Service","Region","Environment","Status","Project"])
 a,b=st.columns(2)
 region=a.selectbox("Region",["All"]+list(assets.Region.unique()))
 env=b.selectbox("Environment",["All"]+list(assets.Environment.unique()))
 if region!="All":assets=assets[assets.Region==region]
 if env!="All":assets=assets[assets.Environment==env]
 st.dataframe(assets,hide_index=True,use_container_width=True)
 section("Planned connectivity")
 st.markdown('<div class="workflow"><span>Secure AWS APIs</span><b>→</b><span>Read-only inventory</span><b>→</b><span>Policy engine</span><b>→</b><span>Asset dashboard</span></div>',unsafe_allow_html=True)

elif page=="Deployments":
 heading("Delivery pipelines","A unified record of CI checks, approval gates and Terraform activity.","DEVOPS ORCHESTRATION")
 a,b,c,d=st.columns(4)
 a.metric("Historical unit tests",43,"Passed")
 b.metric("Actual EC2 test","Verified","Historical")
 c.metric("Duplicate guard","Verified","Historical")
 d.metric("Jenkins status feed","Not connected")
 st.caption("Jenkins was tested locally, but this hosted website has no secure connection to Jenkins on your Mac.")
 section("Deployment architecture","Real tests previously completed; integration not live")
 st.markdown('<div class="tile"><h3>End-to-end controlled deployment</h3><div class="workflow"><span>GitHub PR</span><b>→</b><span>CI checks</span><b>→</b><span>Jenkins dispatch</span><b>→</b><span>AWS duplicate check</span><b>→</b><span>Terraform plan</span><b>→</b><span>Approval</span><b>→</b><span>Apply</span></div></div>',unsafe_allow_html=True)
 section("Historical verification","Prior Jenkins logs")
 st.dataframe(pd.DataFrame([
 ["New EC2 request","Completed","Human approval + Terraform apply"],
 ["Second employee duplicate","Blocked intentionally","No extra EC2 created"],
 ["Automatic SCM triggering","Completed","Dispatcher queued downstream CI/CD"],
 ["Automatic duplicate request","Blocked intentionally","Apply stage skipped"]],columns=["Scenario","Observed outcome","Evidence summary"]),hide_index=True,use_container_width=True)
 st.link_button("View Jenkins pipeline code","https://github.com/wavhalkomal/Terraform_Jenkins")
 section("Live GitHub Actions","Read-only API · refreshes every 90 seconds")
 gh=github_status()
 if gh["connected"]:
  st.success("Connected to the public GitHub Actions API. These are real workflow runs.")
  if gh["runs"]:
   st.dataframe(pd.DataFrame(gh["runs"]),hide_index=True,use_container_width=True,
                column_config={"Run URL":st.column_config.LinkColumn("Open run")})
  else:
   st.info("No workflow runs found.")
 else:
  st.warning(gh["error"] or "GitHub API unavailable")
 st.caption("GitHub Actions results are live; Jenkins on your Mac and AWS are not connected to this portal.")

elif page=="Integrations & Access":
 heading("Integrations & Access","Organization administrators configure company-owned services; employees use a single authorized login.","ENTERPRISE ACCESS CONTROL")
 st.info("This is the integration onboarding blueprint. Public visitors cannot enter or validate credentials here because an authenticated, isolated backend is not yet deployed.")
 gh=github_status()
 section("Provider connection status","Actual web portal connections — not historical CI/CD tests")
 providers=pd.DataFrame([
  ["CloudLaunch SSO","Not configured","Identity provider OIDC authentication; tenant membership and MFA"],
  ["GitHub Actions (read-only public API)","Connected" if gh["connected"] else "Unavailable","Live public workflow status; no sign-in needed"],
  ["GitHub organization installation","Not configured","Organization admin authorizes a restricted GitHub App installation"],
  ["AWS account","Not configured","Company admin approves scoped cross-account IAM role; backend verifies STS identity"],
  ["Jenkins controller","Not configured","Admin configures a private scoped connector; agent verifies health and job permissions"],
  ["Terraform execution","Not connected to portal","Terraform is run by a controlled Jenkins worker using approved scoped cloud credentials"],
 ],columns=["Provider","Current portal status","How identity / access is verified"])
 st.dataframe(providers,hide_index=True,use_container_width=True)
 section("Credential validation design","Company admin only")
 st.markdown("""**1. Employee signs in with company SSO.** CloudLaunch verifies OIDC ID-token signatures, issuer, audience, expiry, MFA policy and organization membership on the backend.
 
 **2. GitHub:** the organization's administrator authorizes a GitHub App for selected repositories. Backend verifies the installation and its permissions using short-lived installation tokens.
 
 **3. AWS:** the organization's administrator approves a least-privilege cross-account IAM role with an external ID. Backend calls AWS STS `GetCallerIdentity` then restricted read-only inventory APIs to confirm permitted account and scopes. No employee access keys are requested.
 
 **4. Jenkins:** an organization admin installs a restricted outbound connector or enables a secure private integration. Backend verifies TLS, signed responses, allowed jobs and job-specific permissions; never expose your Mac's `localhost:8080` to the public.
 
 **5. Terraform:** no separate end-user Terraform password. Deployment workers receive narrowly scoped short-lived cloud credentials and use isolated remote state and plan approval gates.""")
 section("Go-live security gates")
 st.dataframe(pd.DataFrame([
  ["Organization sign-in and tenant isolation","Required · not implemented"],
  ["Server-side RBAC and approval separation","Required · not implemented"],
  ["Managed secrets and encrypted integration configuration","Required · not implemented"],
  ["Audited, idempotent request queue","Required · not implemented"],
  ["AWS identity + permission scope verification","Required · not implemented"],
  ["Jenkins agent identity + restricted job verification","Required · not implemented"],
  ["Terraform plan guard and duplicate check","Existing backend tests passed; portal integration pending"],
 ],columns=["Security control","Implementation status"]),hide_index=True,use_container_width=True)
 st.warning("No AWS secret keys, Jenkins admin tokens or individual user passwords should be pasted into this public app.")
 st.link_button("View enterprise integration design","https://github.com/wavhalkomal/Terraform_Jenkins/blob/main/docs/ENTERPRISE_AUTH_AND_INTEGRATIONS.md")

elif page=="Cost & Governance":
 heading("Cloud financial operations","Control costs and avoid duplicate, idle or unowned infrastructure.","FINOPS + GOVERNANCE")
 st.info("Every chart and financial amount below is illustrative; real AWS billing is not connected.")
 a,b,c,d=st.columns(4)
 a.metric("Illustrative monthly spend","$735")
 b.metric("Illustrative forecast","$810")
 c.metric("Demo duplicate checks","1")
 d.metric("Cost Explorer API","Not connected")
 a,b=st.columns([1.4,1])
 with a:
  with st.container(border=True):
   st.markdown("**Sample cost composition**");st.caption("Example monthly service costs · USD")
   st.plotly_chart(chart("cost"),use_container_width=True,config={"displayModeBar":False})
 with b:
  with st.container(border=True):
   st.markdown("**Governance policy catalog**")
   for name,state in [("Project ownership","Design ready"),("Duplicate protection","Backend tested"),("Spend alerts","Planned"),("Budget approvals","Planned"),("Idle server cleanup","Planned")]:
    st.markdown(f"**{name}** — {state}")
 st.caption("Only approved, authenticated backends should perform cloud actions or report real company costs.")

else:
 heading("Product architecture","A secure modular architecture, built on top of the tested CloudLaunch automation engine.","ENGINEERING FOUNDATION")
 layers=[
 ("01","Streamlit experience","Public product UI and self-service forms · demo available"),
 ("02","FastAPI + enterprise SSO","Secure APIs, user roles and authorization · planned"),
 ("03","PostgreSQL + durable workflows","Persistent tickets, retry handling and audit trail · planned"),
 ("04","Jenkins + Terraform + boto3","Automated infrastructure provisioning and duplicate checks · independently tested"),
 ("05","AWS observability + FinOps","Live health, inventory and billing · planned")]
 for num,name,desc in layers:
  st.markdown(f'<div class="tile" style="min-height:85px;padding:16px"><span class="chip">{num}</span><h3 style="display:inline;margin-left:12px">{name}</h3><p style="margin:9px 0 0">{desc}</p></div>',unsafe_allow_html=True)
 st.info("The production enterprise platform requires an authenticated, persistent backend. Streamlit Community Cloud is used for a no-cost public showcase.")

st.markdown('<div class="small" style="text-align:center;margin-top:35px">Copyright © Komal Wavhal 2026</div>',unsafe_allow_html=True)
