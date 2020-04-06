Contains Clarity scripts that use the clarity-ext framework at https://github.com/molmed/clarity-ext

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
