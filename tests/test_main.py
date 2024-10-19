# -*- coding: utf-8 -*-
import datetime

import pytest

from file_automation.config import RenderedPresetConfig, RenderedTargetConfig
from file_automation.main import get_target_matches, get_templating_context


def test_get_templating_context(tmp_path):
    path = tmp_path / "test.howdy"
    path.write_text("howdy")

    preset = RenderedPresetConfig(name="test_preset", command="foo", vars={"var1": "var1"}, rename="foo/{preset}{ext}")
    target = RenderedTargetConfig(name="test_target", glob="test", presets=[preset], vars={"var2": "var2"})

    context = get_templating_context(path, target, preset)

    datetime.date.fromisoformat(context["date"])
    datetime.time.fromisoformat(context["time"])
    datetime.date.fromisoformat(context["created_at_date"])
    datetime.date.fromisoformat(context["modified_at_date"])

    assert context["input_path"] == str(path)
    assert context["stem"] == "test"
    assert context["suffix"] == ".howdy"
    assert context["ext"] == ".howdy"
    assert context["parent"] == str(tmp_path)
    assert context["parent_parent"] == str(tmp_path.parent)
    assert context["name"] == "test.howdy"
    assert context["preset"] == "test_preset"
    assert context["target"] == "test_target"
    assert context["var1"] == "var1"
    assert context["var2"] == "var2"
    assert context["output_path"] == r"foo\test_preset.howdy"


@pytest.mark.parametrize(
    ["files", "glob", "options", "expected"],
    [
        pytest.param([], "foo/*", {}, set(), id="empty"),
        pytest.param(
            ["foo.txt", "bar.mp3", "foo.JpeG"],
            "{tmp_path}/*",
            {"include_ext": [".txt", ".jpeg"]},
            {"foo.JpeG", "foo.txt"},
            id="Check include_ext",
        ),
        pytest.param(
            ["foo.txt", "bar.MP3", "foo.jpeg"],
            "{tmp_path}/*",
            {"exclude_ext": [".mp3"]},
            {"foo.jpeg", "foo.txt"},
            id="Check exclude_ext",
        ),
        pytest.param(
            ["foo.txt", "bar BaD.txt"],
            "{tmp_path}/*",
            {"exclude_keywords": ["BAD"]},
            {"foo.txt"},
            id="Check exclude_keywords",
        ),
    ],
)
def test_get_target_matches(files, glob, options, expected, tmp_path):
    for file in files:
        (tmp_path / file).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / file).write_text("foo")

    target = RenderedTargetConfig(
        name="test",
        glob=glob.format(tmp_path=tmp_path),
        presets=[RenderedPresetConfig(name="test", command="foo")],
        **options,
    )

    result = {p.name for p in get_target_matches(target)}
    assert result == expected
