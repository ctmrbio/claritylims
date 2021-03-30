# claritylims
Customizations for our GenoLogics BaseSpace Clarity LIMS 

These are located on the server in the directory `/opt/gls/clarity/customextensions`

## Permissions
The owner of this directory is user `glsjboss` and the group `claritylims`.

All files and directories in this directory should be created and modified as
the `glsjboss` user.

All git commands (commits, push, pull) should be done as your own user (that
is, `su user.name` or log in as your own user and then run the relevant git
commands.

To be able to do this, your user should be added to the `claritylims` group:

    usermod -a -G claritylims user.name

You will need to log in and out to apply this change.

You may also need to adjust the write permissions on the `.git` directory to
allow the group to write to it:

    sudo chmod -R 775 .git

In the case that you want to commit as your own user from the `glsjboss` user,
there is this command:

    GIT_COMMITTER_NAME="New Name" GIT_COMMITTER_EMAIL="name@email.com" git commit --author="New Name <name@email.com>"

## Automations
The automations here are input into the LIMS through the web interface.

They should first be modified through the files in this directory, and then
copy-pasted into the web interface. This of course isn't always going to be the
most practical workflow when playing around with automations, but it is
recommended in order to keep the automations up to date in the git repository.
Alternatively, one could copy paste from the web interface into the repository
once sure the automation is sound, and then commit the changes.

The basic layout of an automation file should look like this:

    # Clarity LIMS 5.0 Automation
    ## Modify the command in here first, and then copy-paste to the web interface.
    ## This will help keep the git repository up to date.

    ### Automation Name:
    Assign QC Flags

    ### Creation date:
    2018-03-09

    ### Author:
    Kim Wong

    ### Enabled on master steps:
    PicoGreen QC (DNA) 5.0
    QuantIt BroadRange
    QuantIt HighSensitivity

    ### Command:
    bash -c "python /opt/gls/clarity/customextensions/assignqcflags.py -u {username} -p {password} -o '{udf:Criteria 1 - Operator}' -t '{udf:Criteria 1 - Threshold Value}' -a '{artifactsURI:v2}' -x '{outputFileLuids}'"

Make sure this file is updated to reflect changes in the web interface!

## Genologics package
Scripts in Python are much easier to write with the [SciLifeLab Genologics
package](https://github.com/SciLifeLab/genologics). This was installed through
`./pip install genologics` (not `./conda install genologics` as it doesn't
exist in the conda repos) in the Miniconda environment
`/opt/gls/clarity/miniconda3/bin`.

The config file for this package is found at `/etc/genologics.conf`, owned by
root but readable for other users.

## The clarity-ext package

The [clarity-ext](https://github.com/molmed/clarity-ext) package is designed to
make writing extensions that are easier to read an simple to write. They have a
higher level of abstraction than the genologics package, which has a 1-1
mapping to the REST API. Some of the scripts (all related to Covid19) are
written using that framework.

Extensions that use this framework are all in ./clarity-ext-scripts. Refer to
the [README](./clarity-ext-scripts/README.md) for more information on this
package.

## SmiNet 
There is a client for SmiNet integration in ./sminet_client/. Refer to the
[README](./sminet_client/README.md) for more information on the package.

## More information
More information about the LIMS system including details on the Miniconda
installation and starting the server may be found
[here](https://github.com/ctmrbio/wiki/wiki/CTMR-LIMS-(PROD-and-STAGE)).
