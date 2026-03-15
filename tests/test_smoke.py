from pathlib import Path

from typer.testing import CliRunner

from imx.main import app


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Image X-tool CLI" in result.stdout


def test_colorize_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["colorize", "--help"])
    assert result.exit_code == 0
    assert "--cmap" in result.stdout
    assert "--force-color" in result.stdout


def test_blend_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["blend", "--help"])
    assert result.exit_code == 0
    assert "--black-transparent" in result.stdout
