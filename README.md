# Splice Sample Organizer

This project aims to bring some order to the sample files downloaded via Splice without having to use the GUI. Provide a target structure along with predicates for each folder in order to symlink all your splice samples into the shape you want.

Originally this was a fork of [Splorganizer](https://github.com/ebai101/splorganizer) but has since then evolved into a way more customizable utility.

## Get started

#### Download Sample Data

This project uses the splice log utility to obtain data about your sample library. In order to use it, you need to download the logs locally. You can do this by going to Splice -> Settings -> Utilities -> Download logs.

They normally end up in your downloads folder.

#### Configure

To use the oragnizer tool, clone the repo and setup the following files:

1. `config/config.yaml`

Specifies the input and output directories along with some metadata. 

- `username: <splice username>`
- `sorted_dir: <output directory>`
- `zip_dir: <directory where your splice logs are located>`
- `zip_fuzzy: SpliceLogs`
- `log_dir: <debug directory for logs>`

2. `config/hierarchy.yaml`

Specifies the target hierarchy for the output folder. The each entry in this file gets translated into a folder in the output directory. Each folder definition contains a name along with predicates. These can be one of the following:

- `tag_regex: tag regexp`
- `file_regex: filename regexp`
- `key_regex: audio_key | filename regexp`
- `sample_type: loop | oneshot`
- `where: custom SQL predicate`

The folder definition can also specify another `dirs` property with subfolder. Try running it with the default hierarchy and compare the output to the configuration.

#### Install dependencies

The project uses poetry so you should be able to simply run `poetry install`.

#### Run

Run the project with `poetry run python src/main.py`

The available flags for the scrpit are as follow:

- `--keep/--no-keep` (default = False): If true, keeps the Splice log files. If false, removes them upon running the script.
- `--reset/--no-reset` (default = True): If true, resets the output directory and starts from scratch. If false, tries to merge the existing files in the output directory with any potentially new files.

