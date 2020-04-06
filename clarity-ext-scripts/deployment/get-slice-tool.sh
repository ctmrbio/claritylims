#!/bin/bash

# Usage: ./get-slice-tool <USER>@<SERVERNAME>

mkdir -p ./bin
scp -r $1:/opt/gls/clarity/tools/config-slicer/ ./bin/

