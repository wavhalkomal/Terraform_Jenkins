"""Read-only public GitHub workflow telemetry for CloudLaunch.

No token, Jenkins URL, or AWS credentials required. Remote failures fail closed:
callers receive an explicit unavailable state, never fictional success.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://api.github.com/repos/wavhalkomal/Terraform_Jenkins/actions/runs?per_page=12"
ALLOWED_STATES = {"queued", "in_progress", "completed", "requested", "waiting", "pending"}

def normalize_run(item):
    """Only expose a narrow, validated subset of public workflow metadata."""
    if not isinstance(item, dict):
        return None
    url = item.get("html_url", "")
    if not isinstance(url, str) or not url.startswith(
        "https://github.com/wavhalkomal/Terraform_Jenkins/actions/runs/"
    ):
        return None
    return {
        "Workflow": str(item.get("name") or "Unnamed")[:120],
        "Status": str(item.get("status") or "unknown")[:30],
        "Result": str(item.get("conclusion") or "Pending")[:30],
        "Branch": str(item.get("head_branch") or "unknown")[:80],
        "Started (UTC)": str(item.get("created_at") or "")[:22],
        "Run URL": url,
    }

def fetch_workflows(timeout=6):
    """Return {'connected':bool, 'runs':list, 'error':str|None}."""
    request = Request(
        API,
        headers={"Accept":"application/vnd.github+json",
                 "User-Agent":"CloudLaunch-Public-Status/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.load(response)
        if not isinstance(data, dict) or not isinstance(data.get("workflow_runs"), list):
            return {"connected":False,"runs":[],"error":"GitHub returned an unexpected response"}
        runs = [r for item in data["workflow_runs"] if (r := normalize_run(item))]
        return {"connected":True,"runs":runs,"error":None}
    except (HTTPError, URLError, OSError, ValueError, TypeError, TimeoutError) as exc:
        return {"connected":False,"runs":[],"error":f"GitHub workflow API unavailable ({type(exc).__name__})"}
