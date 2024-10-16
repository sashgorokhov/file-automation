# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

import pydantic
import yaml


CONFIG_ENV_VAR = "FFM_CONFIG"


# These configs are for human beings
class PresetConfig(pydantic.BaseModel):
    command: str = pydantic.Field(
        description='Required. Command will be rendered using variables available in templating context. See "Templating context reference"'
    )
    rename: Optional[str] = pydantic.Field(
        description='Optional. If your command creates new files, you can specify this parameter that will be used as new file name. Result of rendering this template will be available as "output_path" variable in command template. Command will not run if "output_path" file exists.'
    )
    vars: Dict[str, str] = pydantic.Field(
        default_factory=dict,
        description="Optional. Any additional variables to pass into command template. Will override all other built-in variables and targets variables too.",
    )


class TargetConfig(pydantic.BaseModel):
    glob: str = pydantic.Field(
        description="Required. Pattern for file matching. Supports standard globbing syntax like *, ?, **"
    )
    include_ext: Set[str] = pydantic.Field(
        default_factory=set, description="Optional. ONLY match files with these extensions."
    )
    exclude_ext: Set[str] = pydantic.Field(
        default_factory=set, description="Optional. Exclude files that have these extensions."
    )
    exclude_keywords: Set[str] = pydantic.Field(
        default_factory=set,
        description="Optional. Exclude files that have these keywords in their name (case-insensitive)",
    )
    presets: List[str] = pydantic.Field(
        default_factory=list,
        min_length=1,
        description='Required. List of preset names from "presets" config that will be applied to each matched file.',
    )
    vars: Dict[str, str] = pydantic.Field(
        default_factory=dict,
        description="Optional. Minimum time in seconds that passed since file modification to consider it as match.",
    )
    min_age_s: int = pydantic.Field(
        default=60,
        ge=0,
        description="Optional. Any additional variables to pass into command template. Will override all other built-in variables.",
    )


class Config(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    presets: Dict[str, PresetConfig] = pydantic.Field(default_factory=dict)
    targets: Dict[str, TargetConfig] = pydantic.Field(default_factory=list)

    @pydantic.model_validator(mode="after")
    def check_presets_exist(self):
        for target_name, target in self.targets.items():
            for preset in target.presets:
                if preset not in self.presets:
                    raise ValueError(
                        f'Target "{target_name}" validation error: '
                        f'Using preset "{preset}" but it is not defined in presets: {list(self.presets.keys())}'
                    )
        return self


def load_config_file_or_env(file: Optional[Path], env: str) -> Config:
    if not file:
        if env not in os.environ:
            raise EnvironmentError(f'Environment variable "{env}" is not defined')
        file = Path(os.environ[env])

    if not file.exists():
        raise FileNotFoundError(f'Config "{file}" does not exist')

    with file.open("r") as f:
        return Config.model_validate(yaml.safe_load(f))


# And these configs are for machine spirits
class RenderedPresetConfig(pydantic.BaseModel):
    name: str
    command: str
    rename: Optional[str] = None
    vars: Dict[str, str] = pydantic.Field(default_factory=dict)


class RenderedTargetConfig(pydantic.BaseModel):
    name: str
    glob: str
    include_ext: Set[str] = pydantic.Field(default_factory=set)
    exclude_ext: Set[str] = pydantic.Field(default_factory=set)
    exclude_keywords: Set[str] = pydantic.Field(default_factory=set)
    presets: List[RenderedPresetConfig] = pydantic.Field(default_factory=list, min_length=1)
    vars: Dict[str, str] = pydantic.Field(default_factory=dict)
    min_age_s: int = pydantic.Field(default=60, ge=0)


# Converts human configs into machine configs
def build_rendered_target_configs(config: Config) -> List[RenderedTargetConfig]:
    result: List[RenderedTargetConfig] = []

    for target_name, target in config.targets.items():
        presets = [
            RenderedPresetConfig(
                name=preset_name,
                **config.presets[preset_name].model_dump(),
            )
            for preset_name in target.presets
        ]

        result.append(RenderedTargetConfig(name=target_name, presets=presets, **target.model_dump()))

    return result
