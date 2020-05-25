#!/bin/bash

# Sets up socks for connecting via the stage server as a jump host
# This allows you to run the integration tests for sminet.
# Setup:
#  - Make sure that you have an entry for ctmr-lims-stage in ~/.ssh/config similar to
#    Host ctmr-lims-stage
#        HostName <HOSTNAME>
#        User <USERAME>
#        IdentityFile ~/.ssh/ctmr-lims-stage
#  - You or your sysadmin must have added the key ~/.ssh/ctmr-lims-stage to authorized_keys for your
#    user on ctmr-lims-stage.
#  - You must have a proxy entry in ~/.config/clarity-ext/clarity-ext.config on the format:
#    sminet_proxy: socks5://localhost:8123

echo "Killing old instances..."
kill -9 $(lsof -i:8123 -t) 2> /dev/null

echo "SSHing using SOCKS protocol on port 8123..."
ssh -D 8123 -f -C -q -N ctmr-lims-stage 

