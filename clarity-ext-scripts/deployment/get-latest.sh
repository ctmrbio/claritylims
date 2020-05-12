#!/bin/bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Fetches latest. This script is intended to be run in a cron job on the server

# Pulls the latest version from the dev branch
branch=dev

cd $SCRIPT_DIR/claritylims

sha1=$(git rev-parse HEAD)
git fetch
git checkout $branch
git reset --hard origin/$branch
sha2=$(git rev-parse HEAD)

if [ "$sha1" != "$sha2" ]; then

cd clarity-ext-scripts
source /opt/gls/clarity/miniconda3/bin/activate clarity-ext
./setup.sh

else
echo "Nothing to do for $sha1"
fi
