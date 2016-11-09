
Using the GCP Plugin with a Manager
===================================

Bootstrapping
-------------

Use the `simple manager blueprint`_ to bootstrap a manager
on a CentOS 7 Instance with at least 4GB of RAM.

.. _simple manager blueprint: http://docs.getcloudify.org/latest/manager/bootstrapping

In order for the blueprint to complete validation, it is necessary to add the ``Instance``'s own external IP address to a Firewall Rule permitting http traffic to the ``Instance``.

.. _manager-config:

Manager GCP Config
------------------
If you don't want to provide the ``gcp_config`` dictionary to every node in your blueprints, you can provide it, as ``yaml`` at ``/etc/cloudify/gcp_plugin/gcp_config``.

See :ref:`account-info` for details on the contents of the ``gcp_config`` file.

Networks
--------
Instances in GCP are not able to communicate internally with instances in a different network.
This means that if you want to run Cloudify agents on your nodes they must be in the same network as the manager.

Additionally, a given network must choose either auto-subnets or manual subnets operation when created.
For maximum flexibility, ``auto_subnets = false`` is recommended, though this requires that subnets are created for any region you wish to place instances in.
