# claritylims
Customizations for our GenoLogics BaseSpace Clarity LIMS 

These are located on the server in the directory `/opt/gls/clarity/customextensions`

## Permissions
The owner of this directory is user `glsjboss` and the group `claritylims`.

All files and directories in this directory should be created and modified as the `glsjboss` user.

To be able to push and pull from the git repository as your own user, your user should be added to
the `claritylims` group:

    `usermod -a -G claritylims user.name`
You will need to log in and out to apply this change.

You may also need to adjust the write permissions on the `.git` directory to allow the group to write to it. 

To commit as another user (such as your own, from the `glsjboss` user), it may be necessary to use 
this command:

    GIT_COMMITTER_NAME="New Name" GIT_COMMITTER_EMAIL="name@email.com" git commit --author="New Name <name@email.com>"

## Automations
The automations here are input into the LIMS through the web interface.

They should first be modified through the files in this directory, and then copy-pasted into the web 
interface. This of course isn't always going to be the most practical workflow when playing around
with automations, but it is recommended in order to keep the automations up to date in the git 
repository. Alternatively, one could copy paste from the web interface into the repository once
sure the automation is sound, and then commit the changes.

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
