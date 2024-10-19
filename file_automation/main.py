# -*- coding: utf-8 -*-
import argparse
import datetime
import glob
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterator, List

from file_automation.config import (
    CONFIG_ENV_VAR,
    Config,
    RenderedPresetConfig,
    RenderedTargetConfig,
    build_rendered_target_configs,
    load_config_file_or_env,
)


logger = logging.getLogger(__name__)


def entrypoint():
    """Script entrypoint function"""
    logging.basicConfig(level=logging.DEBUG)
    cli(sys.argv[1:])


def main(config: Config):
    target_configs = build_rendered_target_configs(config)

    for target in target_configs:
        logger.debug(f'Processing target "{target}": {target}')

        for path in get_target_matches(target):
            for preset in target.presets:
                apply_target_preset(path, target, preset)


def get_target_matches(target: RenderedTargetConfig) -> Iterator[Path]:
    """
    Return list of absolute file paths that are matched by target
    """
    for match in glob.iglob(target.glob, recursive=True):
        path = Path(match)

        if target.include_ext and path.suffix.lower() not in target.include_ext:
            logger.debug(f"{target.name} Skipping {path}, not in include_ext")
            continue

        if path.suffix.lower() in target.exclude_ext:
            logger.debug(f"{target.name} Skipping {path}, in exclude_ext")
            continue

        for keyword in target.exclude_keywords:
            if re.match(keyword, str(path.name), re.IGNORECASE):
                logger.debug(f'{target.name} Skipping {path}, contains "{keyword}" from exclude_keywords')
                continue

        stat = path.stat()

        if target.min_age_s and (time.time() - stat.st_mtime) < target.min_age_s:
            logger.debug(f"{target.name} Skipping {path}, not old enough")
            continue

        yield path


def apply_target_preset(path: Path, target: RenderedTargetConfig, preset: RenderedPresetConfig):
    """
    Render presets command for given file and execute it
    """
    command = preset.command
    context = get_templating_context(path, target, preset)

    if "output_path" in context:
        if Path(context["output_path"]).exists():
            logger.debug(f'Skipping {path}, already exists at {context["output_path"]}')
            return
        Path(context["output_path"]).parent.mkdir(parents=True, exist_ok=True)

    try:
        command_rendered = command.format(**context)
    except:
        raise ValueError(f'Failed to render: "{command}". Available context: {context}')

    run_command(command_rendered)


def run_command(command: str):
    logger.info(f"Running: {command}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if result.returncode != 0:
        print(result.stdout.decode())
        print(result.stderr.decode())


def get_templating_context(path: Path, target: RenderedTargetConfig, preset: RenderedPresetConfig) -> Dict[str, str]:
    """
    Create context dictionary for template rendering.

    :param path: Path that we are creating context for
    :param target: RenderedTargetConfig
    :param preset: RenderedPresetConfig
    """
    stat = path.stat()

    custom_variables: Dict[str, str] = {**target.vars, **preset.vars}

    general_variables: Dict[str, str] = {
        "date": datetime.date.today().isoformat(),
        "time": datetime.datetime.now().time().isoformat("seconds"),
    }

    path_variables: Dict[str, str] = {
        "created_at_date": datetime.datetime.fromtimestamp(stat.st_ctime).date().isoformat(),
        "modified_at_date": datetime.datetime.fromtimestamp(stat.st_mtime).date().isoformat(),
        "input_path": str(path),
        "stem": path.stem,
        "suffix": path.suffix,
        "ext": path.suffix,
        "parent": str(path.parent),
        "parent_parent": str(path.parent.parent),
        "name": path.name,
    }

    target_variables: Dict[str, str] = {
        "target": target.name,
    }

    preset_variables: Dict[str, str] = {
        "preset": preset.name,
    }

    context = {**general_variables, **path_variables, **target_variables, **preset_variables, **custom_variables}

    if preset.rename:
        try:
            output_path = Path(preset.rename.format(**context))
        except:
            raise ValueError(f'Failed to render: "{preset.rename}". Available context: {context}')

        context["output_path"] = str(output_path)

    return context


def cli(argv: List[str]):
    """
    Command line parsing and main logic execution in the loop

    :param argv: command line arguments for parsing
    """
    parser = argparse.ArgumentParser(
        description="File Automation - run templated shell commands for each file matched by pattern."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help=f"Optional. Specify path to yaml config file. Can also use env {CONFIG_ENV_VAR}",
    )
    parser.add_argument(
        "--loop",
        type=int,
        help='Instead of running one time and existing, this will make script to run every "loop" seconds. '
        "It will try to load config every time it runs so changes to configuration do not require script restart.",
    )

    args = parser.parse_args(argv)
    config_path = args.config
    loop = args.loop

    while True:
        config = load_config_file_or_env(config_path, env=CONFIG_ENV_VAR)

        main(config)

        if not loop:
            break

        time.sleep(loop)


if __name__ == "__main__":
    entrypoint()
