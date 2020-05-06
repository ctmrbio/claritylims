Contains Clarity scripts that use the clarity-ext framework at https://github.com/molmed/clarity-ext

# clarity-ext

Usage:

- install-req.sh (only when setting up)
- Activate your virtual environment (must be python 2)
- setup.sh

These scripts require the libraries clarity-ext and its version of genologics. Both are included
as submodules, and will be updated by calling setup.sh.

Special note for covid19: In order to update these requirements for now, make PRs into the
branch `covid` on:

    https://github.com/Molmed/clarity-ext
    https://github.com/Molmed/genologics

and make sure to `git add` these commit references in this repository.

# Releasing to production:

Releasing to the productions servers concists of two major steps. Pushing the script changes,
and push the config changes, to the production server. The first one is carried out by:

1. Merging the `dev` branch to the `prod` branch. When this has happened, these changes should within a minute be
   pushed to the production server.
2. Creating a release on the `prod` branch with accompaniying release notes, using the Github web interface.

For details on how to release the configuration changes see "Exporting configuration".

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

    python ./slices.py import prod --validate <package file>

Read through the results and ensure that there are no warnings or errors. If ready, call:

    python ./slices.py import prod <package file>

## Save the history

    zip import-v1-prod.zip configslicer.log exports/*
    scp import-v1-prod.zip glsai@ctmr-lims-stage:/opt/gls/clarity/users/glsai/deployment/history/

# Import samples format

Samples are imported by uploading a CSV file to the step `Covid19 Create samples`. First, add
a control to the step. It will not be used, it's just there because Clarity requires a sample in
order to start a workflow.

We assume that the samples are in a plate.

The CSV file must have these fields:

    * name: Name of the sample
    * well: The alphanum index of the sample (e.g. A1 or A:1)

Example:

```
name,well
sample1,A1
neg_rna,A2
```

Furthermore, the research engineer must provide the following step UDFs:

    * Assign to workflow: The name of the workflow to which the samples should be added
    * Project: The name of the project

Other step UDFs are not required as they have defaults, but can be set e.g. for test purposes:

    * Sample name: The format of the sample name. The user may specify the dynamic fields:
        * {name}: The original name in the CSV
        * {date:<python format>}: The timestamp when the test started, formatted as a string according to
          python date and time format specifiers which are documented [here](https://strftime.org/)
        * {index}: The index of the sample in the batch (running number)
    * Control name: The format of the control name. Provides the same fields as Sample name.
    * Container name: Format of the container name. Can use these fields:
        * {name}: Sampe as for Sample name
        * {date:<python format>}: Same as for Sample name
    * Control mapping: A comma separated list of mappings from a pattern that matches controls in the name field in the CSV
      and returns the value that should be added to the UDF "Control type".
    * Container type: Defaults to 96 well plate
