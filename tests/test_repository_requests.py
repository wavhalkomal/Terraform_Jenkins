import unittest
from io import BytesIO
from unittest.mock import patch
from cloudlaunch_portal.repository_requests import fetch_request_files

class ContextResponse:
 def __init__(self,request_id):
  self.request_id=request_id
 def __enter__(self):
  import json
  return BytesIO(json.dumps({"request_id":self.request_id,
    "workload":"payment-api","environment":"dev","region":"us-east-1",
    "instance_type":"t3.micro","employee_id":"rahul"}).encode())
 def __exit__(self,*args):return False

class RepositoryRequestsTests(unittest.TestCase):
 @patch("cloudlaunch_portal.repository_requests.urlopen")
 def test_three_real_file_records(self,fetch):
  fetch.side_effect=lambda req,timeout:ContextResponse(req.full_url.rsplit("/",1)[-1][:-5])
  result=fetch_request_files()
  self.assertTrue(result["connected"])
  self.assertEqual(len(result["rows"]),3)
  self.assertIn("later deleted",result["rows"][0]["Historical result"])
 @patch("cloudlaunch_portal.repository_requests.urlopen")
 def test_api_error_fails_closed(self,fetch):
  fetch.side_effect=OSError("offline")
  result=fetch_request_files()
  self.assertFalse(result["connected"])
  self.assertEqual(result["rows"],[])
