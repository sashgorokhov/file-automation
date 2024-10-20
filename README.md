# File Automation

[![Test and build](https://github.com/sashgorokhov/file-automation/actions/workflows/test_and_build.yml/badge.svg?branch=main)](https://github.com/sashgorokhov/file-automation/actions/workflows/test_and_build.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/sashgorokhov/file-automation/main)

Run templated shell commands for each file matched by pattern.

## Overview

Use YAML configuration file that defines how to list and match files. For each matched file, program will
execute shell command that is templated using various variables. This program uses two concepts: targets and presets.

Targets:
Each target contains a configration for file matching and list of presets to apply for each matched file.
Use globbing syntax and additional modifiers like extensions to exclude or include, or minimum time passed since modification.

Presets:
Preset is a shell command that will be executed for every file match.

Targets and presets will run in the order of their definition in YAML file.

Shell commands are templated using [python string format syntax](https://docs.python.org/3/library/string.html#format-string-syntax).

## Use cases

Originally I developed this as a simple script to run FFMPEG on my video recordings. The general idea of **file automation**
allowed me to setup a very powerful workflow:
1. Automatically copy all video files from inserted SD card onto a new folder using files modification time
2. Automatically encode those video files into format that is more suitable for video editing
3. Remove encode files that are more than couple months old - I am not going to use them anyway past that
4. Automatically transcode those 4k 120fps video files into smaller 1080p 30fps files optimized for long term storage
5. Delete original files older than 1 year
6. Automatically move any short fragments i cut from main videos, and transcode them to be suitable for telegram
7. Automatically upload those transcoded short fragments into telegram channel

As you can see, this workflow is very powerful yet can be easily expressed and managed by **file automation**.

Currently, it runs on my NAS in docker container built for FFMPEG and hardware accelerated video encoding.

## Configuration reference

```yaml
presets:
  # Order in which presets are defined does not matter. This is a "repository" of available presets.
  move:
    # Required. Command will be rendered using variables available in templating context. See "Templating context reference"
    command: mv "{input_path}" "{output_path}"
    # Optional. If your command creates new files, you can specify this parameter that will be used as new file name.
    # Result of rendering this template will be available as "output_path" variable in command template.
    # Command will not run if "output_path" file exists.
    rename: {move_dir}/{name}
    # Optional. Any additional variables to pass into command template. Will override all other built-in variables and target's variables too.
    vars:
      foo: bar

targets:
  # Targets definition order matters. Targets are processed one by one in order they are defined.
  move_docs:
    # Required. Pattern for file matching. Supports standard globbing syntax like *, ?, **
    glob: /docs_landing/*
    # Optional. ONLY match files with these extensions. With dot!
    include_ext:
      - .txt
      - .doc
    # Optional. Exclude files that have these extensions. With dot!
    exclude_ext:
      - .mp4
    # Optional. Exclude files that have these keywords in their name (case-insensitive)
    exclude_keywords:
      - billing
    # Optional. Minimum time in seconds that passed since file modification to consider it as match.
    min_age_s: 90
    # Required. List of preset names from "presets" config that will be applied to each matched file.
    presets:
      - move
    # Optional. Any additional variables to pass into command template. Will override all other built-in variables.
    vars:
      move_dir: /docs
```

### Templating context reference

Available variables in `rename` and `command` parameters:

- `date` Current ISO date 2024-01-01
- `time` Current ISO time 23:59:59
- `created_at_date` ISO date when file was created
- `modified_at_date` ISO date when file was last modified
- `input_path` Absolute path that is matched by target and passed through all filters
- `output_path` Available if preset's `rename` parameter is set.
- `stem` File name without extension and folders (for `/foo/bar.txt` stem is `bar`)
- `suffix` **Last** file suffix (extension) **dot included**
- `ext` Same as `suffix`
- `parent` Absolute path to a folder containing matched file
- `parent_parent` Absolute path to folder that contains folder with matched file
- `target` Current target name
- `preset` Current preset name
- `name` File name (with suffix but without folders)

`vars` from preset and target will be also available. Preset's `vars` will take precedence over any other variables defined.

### Command line usage
This is available as command line script:

```shell
> file_automation --help
usage: file_automation [-h] [-c CONFIG] [--loop LOOP]

File Automation - run templated shell commands for each file matched by pattern.

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Optional. Specify path to yaml config file. Can also use env FFM_CONFIG
  --loop LOOP           Instead of running one time and existing, this will make script to run every "loop" seconds.
                        It will try to load config every time it runs so changes to configuration do not require script restart.
```
