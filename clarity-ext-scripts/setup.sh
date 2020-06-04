#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $SCRIPT_DIR/..
git submodule update --init --recursive

cd $SCRIPT_DIR
pip install -e ./repos/clarity-ext/genologics
pip install -e ./repos/clarity-ext

pip install -r $SCRIPT_DIR/requirements.txt
pip install -e $SCRIPT_DIR/.
pip install -e $SCRIPT_DIR/../sminet-client
