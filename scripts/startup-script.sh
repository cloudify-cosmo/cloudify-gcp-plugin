#!/bin/bash

# [START startup_script]
set -e
set -x
apt-get update
apt-get -y install python-dev python-pip

sudo pip install -U pip
sudo pip install virtualenv

MANAGER_IP=$(ip -4 addr show dev eth0 | grep -E '^[[:space:]]*inet' | xargs | awk '{print $2}' | cut -d/ -f1)
SSH_KEY=$HOME/.ssh/key
INPUTS=$HOME/inputs.yaml
BLUEPRINT=$HOME/simple-manager-blueprint.yaml
USER=default

cat << EOF > $SSH_KEY
SSH_PRIVATE_KEY
EOF

cat << EOF >> $HOME/.ssh/authorized_keys
SSH_PUBLIC_KEY

EOF

virtualenv $HOME/env
source $HOME/env/bin/activate

pip install https://github.com/cloudify-cosmo/cloudify-dsl-parser/archive/3.2m6.zip
pip install https://github.com/cloudify-cosmo/cloudify-rest-client/archive/3.2m6.zip
pip install https://github.com/cloudify-cosmo/cloudify-plugins-common/archive/3.2m6.zip
pip install https://github.com/cloudify-cosmo/cloudify-script-plugin/archive/1.2m6.zip
pip install https://github.com/cloudify-cosmo/cloudify-cli/archive/3.2m6.zip

cfy init

wget https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager-blueprints/3.2m6/simple/simple.yaml -O $BLUEPRINT

cat << EOF > $INPUTS
public_ip: $MANAGER_IP
private_ip: $MANAGER_IP
ssh_user: ubuntu
ssh_key_filename: $SSH_KEY

agents_user: $USER
resources_prefix: ''
EOF

cfy bootstrap -p $BLUEPRINT -i $INPUTS --install-plugins
