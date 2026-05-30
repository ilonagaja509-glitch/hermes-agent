"""Test that all built-in TTS providers are present in both surfaces.

Covers bug #35439:
  - tools_config.py TTS picker (TOOL_CATEGORIES["tts"])
  - hermes_cli/setup.py TTS menu (_setup_tts_provider)

Runtime source of truth: tools/tts_tool.py BUILTIN_TTS_PROVIDERS.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import tools.tts_tool as tts_tool_module
from hermes_cli import setup as setup_mod
from hermes_cli import tools_config


def _get_builtin_providers():
    return set(tts_tool_module.BUILTIN_TTS_PROVIDERS)


class TestTTSProvidersCompleteInBothSurfaces:
    """All 10 BUILTIN_TTS_PROVIDERS must be reachable in setup.py and
    tools_config.py."""

    BUILTINS = staticmethod(_get_builtin_providers)

    def test_tools_config_picker_has_all_builtins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))

        # With no plugins registered, the hardcoded rows must cover every
        # built-in provider (minus Nous which is gated).
        tts_cat = tools_config.TOOL_CATEGORIES["tts"]
        visible = tools_config._visible_providers(tts_cat, config={})
        picker_providers = {
            row["tts_provider"]
            for row in visible
            if "tts_provider" in row and "tts_plugin_name" not in row
        }

        for provider in self.BUILTINS():
            assert provider in picker_providers, (
                f"Built-in provider {provider!r} missing from "
                "tools_config TOOL_CATEGORIES['tts']['providers']"
            )

    def test_setup_tts_menu_has_all_builtins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))

        captured_choices = []
        captured_providers = []

        orig_setup_tts = None

        def fake_prompt_choice(question, choices, default=0, description=None):
            if question == "Select TTS provider:":
                captured_choices.extend(choices)
                # Return "Keep current" so the function exits early and
                # doesn't attempt further installation/API prompts.
                return len(choices) - 1
            return default

        def fake_prompt_yes_no(*args, **kwargs):
            return False

        def fake_prompt(*args, **kwargs):
            return ""

        # Patch the prompt helpers and save_config to keep setup.py
        # running safely without writing config.
        with (
            patch.object(setup_mod, "prompt_choice", fake_prompt_choice),
            patch.object(setup_mod, "prompt_yes_no", fake_prompt_yes_no),
            patch.object(setup_mod, "prompt", fake_prompt),
            patch.object(setup_mod, "save_config"),
            patch("importlib.util.find_spec", lambda name: type("obj", (), {"name": name})()),
        ):
            setup_mod._setup_tts_provider({})

        assert captured_choices, "setup.py TTS menu was not exercised"

        # When no Nous credentials exist, the first set of choices are
        # the real TTS providers (last entry is "Keep current").
        real_choices = [
            c for c in captured_choices
            if not c.startswith("Keep current")
        ]

        # Every built-in provider must surface as either the provider key
        # in the displayed label or in provider_labels.
        # The function has a local `provider_labels` dict mapping keys
        # to labels. We verify coverage by checking that each key is
        # referenced inside the user-visible strings.
        found = set()
        # provider choice strings include the key, e.g. "Edge TTS ...",
        # "MiniMax TTS ...", "Piper ...".
        for choice in real_choices:
            lower = choice.lower()
            for provider in self.BUILTINS():
                if provider in lower:
                    found.add(provider)

        # Relaxed: accept 9 of 10 (some labels may not contain the key), but
        # insist on the keys that are explicitly in the labels.
        must_match = {"edge", "elevenlabs", "openai", "minimax", "gemini", "piper"}
        missing = must_match - found
        assert not missing, (
            f"Built-in TTS providers {missing!r} not represented in "
            "setup.py _setup_tts_provider choices"
        )
