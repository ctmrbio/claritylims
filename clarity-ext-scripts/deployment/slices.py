import os
import click
from subprocess import call
import yaml
from datetime import datetime
import logging

logging.basicConfig(level="INFO")

tool = "./bin/config-slicer/config-slicer-3.1.14.7.jar"

# Fetches a manifest file from the staging server

@click.group()
def cli():
    pass

def read_config():
    with open(os.path.expanduser("~/.slices.config"), "r") as fs:
        return yaml.safe_load(fs.read())
config_file = read_config()


@cli.command()
@click.argument("environment")
def manifest(environment):
    config = config_file[environment]
    server = config["server"]
    logging.info("Generating manifest file for {}".format(server))
    manifest_file = "exports/manifest-{}-{}.txt".format(server, datetime.now().isoformat())
    try:
        os.remove(manifest_file)
    except OSError:
        pass
    call(["java", "-jar", tool,
        "-o", "example",
        "-s", server,
        "-u", config["username"],
        "-p", config["password"],
        "-m", manifest_file])


@cli.command()
@click.argument("environment")
def export(environment):
    config = config_file[environment]
    manifest_file = "manifest.txt"
    server = config["server"]
    logging.info("Generating export package for {}".format(server))
    package_file = "exports/export-package-{}-{}.xml".format(server, datetime.now().isoformat())

    call(["java", "-jar", tool,
        "-o", "export",
        "-s", server,
        "-u", config["username"],
        "-p", config["password"],
        "-m", manifest_file,
        "-k", package_file])


@cli.command("import")
@click.argument("environment")
@click.argument("package")
@click.option("--validate/--no-validate", default=False)
def import_package(environment, package, validate):
    operation = "validate" if validate else "importAndOverwrite"
    config = config_file[environment]
    server = config["server"]
    logging.info(
            "Importing export package {} to {} (validate={})".format(package, server, validate))
    call(["java", "-jar", tool,
        "-o", operation,
        "-s", server,
        "-u", config["username"],
        "-p", config["password"],
        "-k", package])

cli()
