#!/bin/bash
set -e

# Fetches latest. This script is intended to be run in a cron job on the server

# Pulls the latest version from the dev branch
branch=0-add-submodule

cd claritylims
git fetch
git checkout $branch
git reset --hard origin/$branch
cd clarity-ext-scripts
source /opt/gls/clarity/miniconda3/bin/activate clarity-ext
./setup.sh
