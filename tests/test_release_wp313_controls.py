"""Regression controls for the private draft and public qualification trust boundary."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    file = ROOT / path
    return file.read_text(encoding="utf-8") if file.is_file() else ""


def jobs(path):
    workflow = source(path)
    if "\njobs:\n" not in workflow:
        return {}
    output = {}
    current = None
    for line in workflow.split("\njobs:\n", 1)[1].splitlines():
        if line.startswith("  ") and not line.startswith("   ") and line.rstrip().endswith(":"):
            current = line.strip()[:-1]
            output[current] = []
        elif current is not None:
            output[current].append(line)
    return {name: "\n".join(lines) for name, lines in output.items()}


class PublicPipeline(unittest.TestCase):
    def test_release_policy_and_replay_state_are_initialized(self):
        policy_path = ROOT / "release-policy.json"
        self.assertTrue(policy_path.is_file(), "release-policy.json must bind both repositories")
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(policy.get("public_repository"), "lmctl-ai/lmpdf")
        self.assertEqual(policy.get("private_repository"), "lmctlhq/lmpdf")
        self.assertTrue((ROOT / "REVOKED").is_file())
        self.assertTrue((ROOT / "release-state.json").is_file())
        self.assertTrue((ROOT / "scripts/release_policy.py").is_file())
        self.assertTrue((ROOT / "scripts/qualification_broker.py").is_file())

    def test_single_trusted_writer_and_read_only_platform_workflow(self):
        private = jobs(".github/workflows/qualify-private-draft.yml")
        worker = jobs(".github/workflows/qualify-platforms.yml")
        self.assertTrue(private, "public broker workflow must exist")
        self.assertTrue(worker, "read-only qualification workflow must exist")
        writers = {name for name, body in private.items() if "contents: write" in body}
        self.assertEqual(writers, {"promote"})
        for name, body in worker.items():
            self.assertNotIn("contents: write", body, name)
            if "actions/checkout@" in body:
                self.assertIn("persist-credentials: false", body, name)
            if name == "candidate":
                self.assertIn("GH_TOKEN:", body)
                self.assertIn("verify-parent-handoff.py", body)
                self.assertNotIn("install-draft-host.py", body)
                self.assertNotIn("check-local-candidate.py", body)
            elif name == "compatibility":
                before_host = body.split("- name: Install the exact draft candidate without credentials", 1)[0]
                candidate_execution = body.split("- name: Install the exact draft candidate without credentials", 1)[1]
                self.assertIn("GH_TOKEN:", before_host)
                self.assertNotIn("GH_TOKEN:", candidate_execution)
            else:
                self.assertNotIn("GH_TOKEN:", body, name)
        worker_workflow = source(".github/workflows/qualify-platforms.yml")
        self.assertIn("repository_dispatch:", worker_workflow)
        self.assertIn("merge-multiple: true", worker_workflow)

    def test_release_authority_controls_are_pinned_and_cancel_safe(self):
        broker = source(".github/workflows/qualify-private-draft.yml")
        block = jobs(".github/workflows/qualify-private-draft.yml").get("promote", "")
        self.assertIn("!cancelled()", block)
        self.assertIn("queue: max", block)
        self.assertIn("verify-parent-handoff.py", source(".github/workflows/qualify-platforms.yml"))
        self.assertIn("SEAL", source("scripts/manage-qualified-draft.py"))
        self.assertIn("recheck(api,root,seal,request,False)", source("scripts/manage-qualified-draft.py"))
        for file in [".github/workflows/qualify-private-draft.yml", ".github/workflows/qualify-platforms.yml", ".github/actions/qualify-platform/action.yml"]:
            for line in source(file).splitlines():
                if "uses:" not in line or "uses: ./" in line:
                    continue
                pin = line.split("uses:", 1)[1].split("#", 1)[0].strip().rsplit("@", 1)[-1]
                self.assertEqual(len(pin), 40, (file, line))

    def test_broker_correlation_title_matches_worker_run_name(self):
        workflow = source(".github/workflows/qualify-platforms.yml")
        broker = source("scripts/qualification_broker.py")
        self.assertIn("run-name: Qualify lmpdf artifact", workflow)
        self.assertIn("title=f'Qualify lmpdf artifact {parent}.{attempt} {tag}'", broker)


if __name__ == "__main__":
    unittest.main()
