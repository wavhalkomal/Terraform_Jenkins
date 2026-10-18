"""Fast repository-level checks. These are not live AWS integration tests."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ("Jenkinsfile", "main.tf", "post_deployment_check.sh"):
            with self.subTest(file=name):
                self.assertTrue((ROOT / name).is_file())

    def test_terraform_exposes_instance_id(self):
        self.assertIn('output "instance_id"', (ROOT / "main.tf").read_text())

    def test_pipeline_requires_approval(self):
        script = (ROOT / "Jenkinsfile").read_text()
        self.assertIn("stage('Manual Approval')", script)
        self.assertIn("stage('Post-Deployment Verification')", script)

    def test_region_consistency(self):
        self.assertIn('region = "us-east-1"', (ROOT / "main.tf").read_text())
        self.assertIn("AWS_REGION         = 'us-east-1'", (ROOT / "Jenkinsfile").read_text())


if __name__ == "__main__":
    unittest.main()
