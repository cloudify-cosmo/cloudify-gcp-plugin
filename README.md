# cloudify-gcp-plugin

* Master [![Circle CI](https://circleci.com/gh/cloudify-cosmo/cloudify-gcp-plugin.svg?style=shield)](https://circleci.com/gh/cloudify-cosmo/cloudify-gcp-plugin)

A Cloudify Plugin that provisions resources in Google Cloud Platform

# cloudfiy-gcp-plugin scripts
## Bootstrap the cloudify manager

To bootstrap the cloudify manager in Google Cloud Platform you need to prepare:
 - client_secret.json file that can be downloaded from cloud developers console
 - generated ssh keys that you want to upload to cloudify manager
 - filled inputs_gcp.yaml.template (renamed to inputs_gcp.yaml) with relevant values 
 
 Simply run:
 ```
 python bootstrap_manager.py
 ```
