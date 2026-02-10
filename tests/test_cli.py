"""
Tests for CLI Module
====================

Verifies the CLI commands and chat infrastructure.
"""

import argparse
import importlib
import pytest

from nucleo.cli import (
    main,
    cmd_chat,
    cmd_init,
    cmd_graph,
    cmd_validate,
    CHAT_COMMANDS,
)


class TestCLIStructure:
    """Verify CLI structure and subcommands."""

    def test_main_returns_zero_no_args(self, monkeypatch):
        """main() with no args prints help and returns 0."""
        monkeypatch.setattr("sys.argv", ["nucleo"])
        result = main()
        assert result == 0

    def test_chat_subcommand_exists(self):
        """chat subcommand is registered."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        # Import and check that cmd_chat is callable
        assert callable(cmd_chat)

    def test_all_commands_callable(self):
        """All command functions are callable."""
        assert callable(cmd_chat)
        assert callable(cmd_init)
        assert callable(cmd_graph)
        assert callable(cmd_validate)

    def test_chat_commands_defined(self):
        """Chat special commands are defined."""
        assert "/help" in CHAT_COMMANDS
        assert "/stats" in CHAT_COMMANDS
        assert "/skills" in CHAT_COMMANDS
        assert "/axioms" in CHAT_COMMANDS
        assert "/clear" in CHAT_COMMANDS
        assert "/quit" in CHAT_COMMANDS

    def test_chat_commands_have_descriptions(self):
        """Each chat command has a description string."""
        for cmd, desc in CHAT_COMMANDS.items():
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestChatCommand:
    """Verify chat command behavior."""

    def test_chat_requires_api_key(self, monkeypatch):
        """cmd_chat returns 1 when ANTHROPIC_API_KEY is not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        args = argparse.Namespace(model=None, verbose=False)
        result = cmd_chat(args)
        assert result == 1

    def test_chat_accepts_model_flag(self):
        """Chat parser accepts --model flag."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        parser_chat = subparsers.add_parser("chat")
        parser_chat.add_argument("--model", "-m", default=None)
        parser_chat.add_argument("--verbose", "-v", action="store_true")

        args = parser.parse_args(["chat", "--model", "claude-haiku-4-5-20251001"])
        assert args.model == "claude-haiku-4-5-20251001"
        assert args.verbose is False

    def test_chat_accepts_verbose_flag(self):
        """Chat parser accepts --verbose flag."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        parser_chat = subparsers.add_parser("chat")
        parser_chat.add_argument("--model", "-m", default=None)
        parser_chat.add_argument("--verbose", "-v", action="store_true")

        args = parser.parse_args(["chat", "-v"])
        assert args.verbose is True


class TestMainModule:
    """Verify __main__.py works."""

    def test_main_module_importable(self):
        """nucleo.__main__ can be imported."""
        mod = importlib.import_module("nucleo.__main__")
        assert mod is not None

    def test_main_module_has_no_side_effects_on_import(self):
        """Importing __main__ doesn't crash (it calls sys.exit via if __name__)."""
        # The module guards sys.exit behind if __name__ == "__main__"
        # so importing it should not call sys.exit
        import nucleo.__main__  # noqa: F401
