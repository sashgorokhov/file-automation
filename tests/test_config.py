# -*- coding: utf-8 -*-
from file_automation.config import Config, PresetConfig, TargetConfig, build_rendered_target_configs


def test_build_rendered_target_configs():
    input_config = Config(
        presets={
            "test1": PresetConfig(command="test1"),
            "test2": PresetConfig(command="test2", rename="foo", vars={"whatever": "1"}),
        },
        targets={
            "test3": TargetConfig(
                glob="foo",
                include_ext=[".mp3"],
                exclude_ext=["jpeg"],
                exclude_keywords=["test"],
                presets=["test1", "test2"],
                vars={"what": "2"},
                min_age_s=55,
            ),
            "test4": TargetConfig(
                glob="foo",
                presets=["test1"],
            ),
        },
    )

    result_target_configs = build_rendered_target_configs(input_config)

    assert len(result_target_configs) == 2

    assert result_target_configs[0].name == "test3"
    assert result_target_configs[1].name == "test4"

    assert len(result_target_configs[0].presets) == 2
    assert len(result_target_configs[1].presets) == 1

    assert result_target_configs[0].presets[0].name == "test1"
    assert result_target_configs[0].presets[1].name == "test2"

    assert result_target_configs[1].presets[0].name == "test1"
