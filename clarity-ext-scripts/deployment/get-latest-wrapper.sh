#!/bin/bash

# Calls ./get-latest.sh, writing output to stdout. This is the script that's set up in the crontab with:
# * * * * * /opt/gls/clarity/users/glsai/deployment/get-latest-wrapper.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

$SCRIPT_DIR/get-latest.sh >> $SCRIPT_DIR/deployment.log
