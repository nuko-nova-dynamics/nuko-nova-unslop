from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks" / "nn_baseline.py"


def run_hook(payload: dict, *, codex: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
    if codex:
        env["PLUGIN_ROOT"] = str(ROOT)
    else:
        env.pop("PLUGIN_ROOT", None)
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=5,
    )


def parsed_output(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)


class HookTests(unittest.TestCase):
    def test_session_start_injects_canonical_baseline(self) -> None:
        result = run_hook({"hook_event_name": "SessionStart"})
        self.assertEqual(result.returncode, 0, result.stderr)
        output = parsed_output(result)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn("every human-facing response", output["additionalContext"])
        self.assertIn("Personality is welcome only in an owned voice", output["additionalContext"])
        self.assertIn("Human does not mean", output["additionalContext"])
        self.assertIn("fake intimacy", output["additionalContext"])
        self.assertLess(len(output["additionalContext"]), 10_000)

    def test_subagent_start_injects_compact_contract(self) -> None:
        result = run_hook({"hook_event_name": "SubagentStart", "agent_type": "Explore"})
        output = parsed_output(result)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SubagentStart")
        self.assertIn("without em dashes", output["additionalContext"])
        self.assertIn("owned or authorized", output["additionalContext"])
        self.assertIn("fake intimacy", output["additionalContext"])
        self.assertIn("profound, cool, quirky, or relatable", output["additionalContext"])

    def test_user_prompt_reminder_is_codex_only_and_small(self) -> None:
        claude = run_hook({"hook_event_name": "UserPromptSubmit", "prompt": "Hello"})
        self.assertEqual(claude.stdout, "")
        codex = run_hook({"hook_event_name": "UserPromptSubmit", "prompt": "Hello"}, codex=True)
        context = parsed_output(codex)["hookSpecificOutput"]["additionalContext"]
        self.assertLessEqual(len(context), 220)
        self.assertIn("no em dashes", context)
        self.assertIn("match the relationship", context)
        self.assertIn("unearned performance", context)

    def test_stop_allows_clean_output(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "last_assistant_message": "The migration passed all checks. I updated the two affected files.",
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_stop_does_not_block_a_supported_tbd_status(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "last_assistant_message": "The launch date remains TBD until the vendor confirms capacity.",
            }
        )
        self.assertEqual(result.stdout, "")

    def test_stop_does_not_block_normal_process_narration(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "last_assistant_message": "I need to analyze the auth flow before changing the middleware.",
            }
        )
        self.assertEqual(result.stdout, "")

    def test_stop_blocks_clear_leaks_once(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "last_assistant_message": "Certainly! The launch slipped -- the vendor missed the date.",
            }
        )
        output = parsed_output(result)
        self.assertEqual(output["decision"], "block")
        self.assertIn("chatbot-artifact", output["reason"])
        self.assertIn("dash-substitute", output["reason"])

    def test_stop_guard_prevents_a_loop(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "stop_hook_active": True,
                "last_assistant_message": "Certainly! This still has a leak — but it may stop now.",
            }
        )
        self.assertEqual(result.stdout, "")

    def test_stop_does_not_hard_block_contextual_cringe_signals(self) -> None:
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "last_assistant_message": (
                    "Plot twist: the migration worked. Chef's kiss. We've all been there, Maya. Trust me on this."
                ),
            }
        )
        self.assertEqual(result.stdout, "")

    def test_stop_handles_a_missing_message(self) -> None:
        result = run_hook({"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual(result.stdout, "")

    def test_unknown_event_fails_open(self) -> None:
        result = run_hook({"hook_event_name": "UnknownEvent"})
        self.assertEqual(result.stdout, "")

    def test_protected_dashes_do_not_block(self) -> None:
        message = 'The contract says, “No prep — no fees.” Use `npm install --save-dev` for 2019–2024 data.'
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "last_assistant_message": message,
            }
        )
        self.assertEqual(result.stdout, "")

    def test_malformed_input_fails_open(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            input="not json",
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
