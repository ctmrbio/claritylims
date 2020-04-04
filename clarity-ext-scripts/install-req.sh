#!/bin/bash

# Changes that must occur once on the server for the installation of
# clarity-ext-scripts

# This script should be run as the user `glsai`
set -e

if [ ! -d /opt/gls/clarity/users/glsai/.conda/envs/clarity-ext ]; then
    /opt/gls/clarity/miniconda3/bin/conda create -n clarity-ext python=2
fi

mkdir -p ~/bin
cp ./deployment/clarity-ext ~/bin/

mkdir -p ~/.config/clarity-ext/
cp ./deployment/clarity-ext.demo.config ~/.config/clarity-ext/clarity-ext.config

# Call setup.sh to install the latest code
