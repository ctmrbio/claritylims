#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

git submodule update --init --recursive
pip install -e ./clarity-ext/genologics
pip install -e ./clarity-ext

pip install -r $SCRIPT_DIR/requirements.txt
pip install -e $SCRIPT_DIR/.
