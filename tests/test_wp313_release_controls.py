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


class PrivatePipeline(unittest.TestCase):
    def test_core_candidate_is_bound_to_private_run_and_throwaway_choice(self):
        candidate = source("scripts/prepare-release-candidate.py")
        verifier = source("scripts/verify-private-build.py")
        freezer = source("scripts/stage-frozen-draft.py")
        self.assertIn("native-release-core/2", candidate)
        self.assertIn("deliberate_failure", candidate)
        self.assertIn("actions/runs/", verifier)
        self.assertIn("EXPECTED_TAG", verifier)
        self.assertIn("stage", freezer)
        self.assertIn("dispatch", freezer)
        self.assertNotIn("--clobber", source("scripts/release-to-public.sh"))

    def test_private_publisher_checks_run_and_attests_frozen_candidate(self):
        workflow = source(".github/workflows/ci.yml")
        self.assertIn("verify-private-build.py", workflow)
        self.assertIn("attest-build-provenance", workflow)
        self.assertIn("stage-frozen-draft.py stage", workflow)
        self.assertIn("stage-frozen-draft.py dispatch", workflow)
        self.assertIn("actions: read", workflow)


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
            self.assertNotIn("GH_TOKEN:", body, name)
            self.assertIn("persist-credentials: false", body, name)
        worker_workflow = source(".github/workflows/qualify-platforms.yml")
        self.assertIn("repository_dispatch:", worker_workflow)
        self.assertIn("merge-multiple: true", worker_workflow)

    def test_release_authority_controls_are_pinned_and_cancel_safe(self):
        broker = source(".github/workflows/qualify-private-draft.yml")
        block = jobs(".github/workflows/qualify-private-draft.yml").get("promote", "")
        self.assertIn("!cancelled()", block)
        self.assertIn("queue: max", block)
        self.assertIn("verify-parent-handoff.py", source("scripts/qualification_broker.py"))
        self.assertIn("FROZEN-CANDIDATE.json", source("scripts/manage-qualified-draft.py"))
        for file in [".github/workflows/qualify-private-draft.yml", ".github/workflows/qualify-platforms.yml", ".github/actions/qualify-platform/action.yml"]:
            for line in source(file).splitlines():
                if "uses:" not in line or "uses: ./" in line:
                    continue
                pin = line.split("uses:", 1)[1].split("#", 1)[0].strip().rsplit("@", 1)[-1]
                self.assertEqual(len(pin), 40, (file, line))


if __name__ == "__main__":
    unittest.main()
