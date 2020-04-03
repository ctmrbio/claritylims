#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

pip install -r $SCRIPT_DIR/requirements-not-pypi.txt
pip install -e $SCRIPT_DIR/.
