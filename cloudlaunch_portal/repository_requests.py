"""Read-only public repository request inventory.

Returns truthful source files and keeps outcomes clearly historical, not current EC2 state.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://raw.githubusercontent.com/wavhalkomal/Terraform_Jenkins/main/requests/"
IDS = ("REQ-1001", "REQ-1002", "REQ-1003")
HISTORICAL_OUTCOMES = {
    "REQ-1001": "Provisioned in verified Jenkins test; instance later deleted",
    "REQ-1002": "Duplicate blocked by AWS check",
    "REQ-1003": "Automatically dispatched; duplicate blocked",
}

def fetch_request_files(timeout=5):
    rows=[]
    try:
        for request_id in IDS:
            req=Request(BASE+request_id+".json",headers={"User-Agent":"CloudLaunch-Portal/1.0"})
            with urlopen(req,timeout=timeout) as response:
                item=json.load(response)
            if not isinstance(item,dict) or item.get("request_id")!=request_id:
                raise ValueError("Unexpected request payload")
            rows.append({
                "Request ID":request_id,
                "Workload":str(item.get("workload",""))[:100],
                "Environment":str(item.get("environment",""))[:40],
                "Region":str(item.get("region",""))[:50],
                "Instance Type":str(item.get("instance_type",""))[:50],
                "Requested By":str(item.get("employee_id",""))[:100],
                "Historical result":HISTORICAL_OUTCOMES[request_id],
            })
        return {"connected":True,"rows":rows,"error":None}
    except (HTTPError,URLError,OSError,ValueError,TypeError,TimeoutError) as exc:
        return {"connected":False,"rows":[],"error":"Request data unavailable ("+type(exc).__name__+")"}
