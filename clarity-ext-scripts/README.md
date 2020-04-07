Contains Clarity scripts that use the clarity-ext framework at https://github.com/molmed/clarity-ext

# clarity-ext

Usage:

* install-req.sh (only when setting up)
* Activate your virtual environment (must be python 2)
* setup.sh

These scripts require the libraries clarity-ext and its version of genologics. Both are included
as submodules, and will be updated by calling setup.sh.

Special note for covid19: In order to update these requirements for now, make PRs into the
branch `covid` on:

    https://github.com/Molmed/clarity-ext
    https://github.com/Molmed/genologics

and make sure to `git add` these commit references in this repository.

# Exporting configuration:

There's a helper script for exporting in the ./deployment directory:

## Get dependencies

First call

    ./get-slice-tool.sh <server>

in order to get the required jar file into your ./bin directory

## Add configuration

Create a yaml configuration file at ~/.slices.config

This configuration file should contain information on this format:

    staging:
      server: server 
      username: username
      password: password 
    prod:
      server: server 
      username: username
      password: password 

## Create a manifest file

Then you can run the slices tool like this:

    python ./slices.py manifest staging  # Creates a new manifest file in your export directory

Copy this manifest file over the file deployment/manifest.txt and remove everything that shouldn't
be imported to production.

## Create a package

Run this to create a package:

    python ./slices.py export staging

This will create a new xml package in the exports directory, which can be imported into production.

## Import a package into production

First call this:

    python ./slices.py import prod --validate

Read through the results and ensure that there are no warnings or errors. If ready, call:

    python ./slices.py import prod

## Save the history

    zip import-v1-prod.zip configslicer.log exports/*
    scp import-v1-prod.zip glsai@ctmr-lims-stage:/opt/gls/clarity/users/glsai/deployment/history/
