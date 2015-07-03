#!/bin/bash

# [START startup_script]
set -e
set -x
apt-get update
apt-get -y install python-dev python-pip

sudo pip install -U pip
sudo pip install virtualenv

USER=default
MANAGER_IP=$(ip -4 addr show dev eth0 | grep -E '^[[:space:]]*inet' | xargs | awk '{print $2}' | cut -d/ -f1)
SSH_KEY=/home/$USER/.ssh/key
INPUTS=/home/$USER/inputs.yaml
BLUEPRINT=/home/$USER/simple-manager-blueprint.yaml
AUTH_LOCATION=/home/$USER/auth

cat << EOF > $SSH_KEY
SSH_PRIVATE_KEY

EOF

cat << EOF >> /home/$USER/.ssh/authorized_keys
SSH_PUBLIC_KEY

EOF

virtualenv /home/$USER/env
source /home/$USER/env/bin/activate

pip install https://github.com/cloudify-cosmo/cloudify-dsl-parser/archive/3.2rc1.zip
pip install https://github.com/cloudify-cosmo/cloudify-rest-client/archive/3.2rc1.zip
pip install https://github.com/cloudify-cosmo/cloudify-plugins-common/archive/3.2rc1.zip
pip install https://github.com/cloudify-cosmo/cloudify-script-plugin/archive/1.2rc1.zip
pip install https://github.com/cloudify-cosmo/cloudify-cli/archive/3.2rc1.zip

cfy init

wget https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager-blueprints/3.2rc1/simple/simple-manager-blueprint.yaml -O blueprint

cat << EOF > inputs
public_ip: 10.0.0.6
private_ip: localhost
ssh_user: vagrant
ssh_key_filename: /home/vagrant/.ssh/id_rsa

agents_user: vagrant
resources_prefix: ''
EOF

cfy bootstrap -p blueprint -i inputs --install-plugins

cat << EOF > $AUTH_LOCATION
AUTH_FILE
EOF
