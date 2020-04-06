#!/bin/bash

# Usage: ./get-slice-tool <SERVERNAME>

mkdir -p ./bin
scp -r $1:/opt/gls/clarity/tools/config-slicer/ ./bin/

