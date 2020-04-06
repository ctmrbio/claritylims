import os
import click
from subprocess import check_call
import yaml
from datetime import datetime

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
    manifest_file = "exports/manifest-{}-{}.txt".format(server, datetime.now().isoformat())
    try:
        os.remove(manifest_file)
    except OSError:
        pass
    check_call(["java", "-jar", tool,
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
    package_file = "exports/export-package-{}-{}.xml".format(server, datetime.now().isoformat())

    check_call(["java", "-jar", tool,
        "-o", "export",
        "-s", server,
        "-u", config["username"],
        "-p", config["password"],
        "-m", manifest_file,
        "-k", package_file])

cli()
