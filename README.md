# LLSub - Language Learner Subtitle Generator

## Overview

`llsub` is a Python script that helps language learners by generating dual-language subtitles. It takes an original SRT subtitle file and translates it to the target language. The translated and original subtitles are then merged line-by-line to assist in language learning.

Specifically, the original language is displayed on the top line and translation is displayed afterward in parenthesis. This means that while watching, you
can read the original language and then check your understanding by reading the translation.

## Note

For best results, ensure that the original subtitle file you are translating is a native
translation of the original audio. It should not be a computer generated transcript or translation.

## Features

- Translates an SRT subtitle file to a target language.
- Optionally merges the original and translated subtitles.

## Installation

### Using pip (Local)

1. Make sure Python 3.x is installed.
2. Install required Python packages in a virtual environment:

    ```bash
    python3 -m venv llsub-env
    source llsub-env/bin/activate  # On Windows, use `llsub-env\Scripts\activate`
    pip install -r requirements.txt
    ```

### As a Python Package

You can also install `llsub` as a Python package for system-wide usage:

1. Clone the repository and navigate to the directory.

    ```bash
    git clone https://github.com/watkins-matt/llsub.git
    cd llsub
    ```

2. Install the package.

    ```bash
    pip install .
    ```

3. You can now use `llsub` from anywhere:

    ```bash
    llsub [--translate-only] input_file [target_language]
    ```

## Usage

To run the script, you can use the following command:

```bash
python llsub.py [-h] [-f] [--translate-only] input_file [target_language]
```

### Arguments

- `--translate-only`: Translate the input file only, do not generate merged subtitles.
- - `-f, --force`: Forcibly overwrites an existing dual language subtitle file if present.
- `input_file`: Path to the input SRT file. Required.
- `target_language`: Target language for translation. Default is `en`.

For example:

```bash
python llsub.py "Episode Name S01E01.sv.srt" en
```
