import json
import unittest
from io import BytesIO
from unittest.mock import patch
from cloudlaunch_portal.github_status import fetch_workflows, normalize_run

class FakeResponse:
    def __init__(self, obj):
        self.body = BytesIO(json.dumps(obj).encode("utf-8"))
    def __enter__(self): return self.body
    def __exit__(self, *args): return False

class GithubStatusTests(unittest.TestCase):
    def test_only_approved_github_run_url(self):
        self.assertIsNone(normalize_run({"html_url":"https://evil.example/run"}))
        self.assertIsNone(normalize_run("bad"))
    @patch("cloudlaunch_portal.github_status.urlopen")
    def test_live_payload(self, urlopen):
        urlopen.return_value = FakeResponse({"workflow_runs":[
            {"html_url":"https://github.com/wavhalkomal/Terraform_Jenkins/actions/runs/123",
             "name":"CloudLaunch CI","status":"completed","conclusion":"success","head_branch":"main"}]})
        result=fetch_workflows()
        self.assertTrue(result["connected"])
        self.assertEqual(result["runs"][0]["Result"],"success")
    @patch("cloudlaunch_portal.github_status.urlopen")
    def test_unavailable_does_not_claim_success(self, urlopen):
        urlopen.side_effect=OSError("unreachable")
        result=fetch_workflows()
        self.assertFalse(result["connected"])
        self.assertEqual(result["runs"],[])
    @patch("cloudlaunch_portal.github_status.urlopen")
    def test_malformed_response_fails_closed(self, urlopen):
        urlopen.return_value=FakeResponse({"workflow_runs":{}})
        self.assertFalse(fetch_workflows()["connected"])
