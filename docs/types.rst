Types
^^^^^


.. _account-info:

Account Information
===================

The plugin needs access to your GCP auth credentials
(via the :ref:`gcp_config <common-properties>` parameter)
in order to operate
(but see :ref:`manager-config` if using a manager).



.. _common-properties:

Common Properties
=================

Many cloud resource nodes have common properties:

``gcp_config``
--------------

Every time you manage a resource with Cloudify,
it creates one or more connections to the GCP API.
The configuration for these clients is specified using the ``gcp_config`` property.
It should be a dictionary with the following values:

  * ``project`` the name of your project on GCP.
  * ``zone`` the default zone which will be used,
    unless overridden by a defined zone/subnetwork.
  * ``auth`` the JSON key file provided by GCP.
    Can either be the contents of the JSON file, or a file path.
    This should be in the format provided by the GCP credentials JSON export (https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount)
  * (optional) ``network`` the default network to place network-scoped nodes in.
    The default network (``default``) will be used if this is not specified.

Example::

    ...
    node_types:
      my_vm:
        type: cloudify.gcp.nodes.Instance
        properties:
          image_id: <GCP image ID>
          gcp_config:
            project: a-gcp-project-123456
            zone: us-east1-b
            auth: <GCP auth JSON file>


``use_external_resource``
-------------------------

Many Cloudify GCP types have a property named ``use_external_resource``, which defaults to ``false``. When set to ``true``, the plugin will apply different semantics for each of the operations executed on the relevant node's instances:

  If ``use_external_resource`` is ``true``, then the required properties for that type (`name`, possibly ``region`` or ``zone``) will be used to look up an existing entity in the GCP project.
  If the entity is found, then its data will be used to popluate the cloudify instance's attributes (``runtime_properties``). If it is not found then the blueprint will fail to deploy.


This behavior is common to all resource types which support ``use_external_resource``:

* ``create`` If ``use_external_resource`` is true, the GCP plugin will check if the resource is available in your account. If no such resource is available, the operation will fail, if it is available, it will assign the resource details to the instance ``runtime_properties``.
* ``delete`` If ``use_external_resource`` is true, the GCP plugin will check if the resource is available in your account. If no such resource is available, the operation will fail, if it is available, it will unassign the instance ``runtime_properties``.


Runtime Properties
------------------

See section on `runtime properties <http://cloudify-plugins-common.readthedocs.org/en/3.3/context.html?highlight=runtime#cloudify.context.NodeInstanceContext.runtime_properties>`_.

Most node types will write a snapshot of the |resource|_
information from GCP when the node creation has finished
(some, e.g. DNSRecord don't correspond directly to an entity in GCP,
so this is not universal).

.. |resource| replace:: ``resource``
.. _resource: https://cloud.google.com/docs/overview/

.. _node_types:

Node Types
==========

The following are
`node type <http://docs.getcloudify.org/latest/blueprints/spec-node-types.md>`_
definitions.
Nodes describe resources in your cloud infrastructure.


Types
=====

Compute
-------

.. cfy:node:: cloudify.gcp.nodes.Instance

    A GCP Instance (i.e. a VM).


.. cfy:node:: cloudify.gcp.nodes.Address

    A GCP Address. This can be connected to an Instance using the
    ``cloudify.gcp.relationships.instance_connected_to_ip`` relationship type


.. cfy:node:: cloudify.gcp.nodes.ExternalIP

    *Deprecated* use the ``external_ip`` property on the ``Instance``
    or an ``Address`` node instead.

    When used with the ``cloudify.gcp.relationships.instance_connected_to_ip`` the connected Instance will be created with an ephemeral external IP.


.. cfy:node:: cloudify.gcp.nodes.Volume

    A GCP Volume.

    A virtual disk which can be attached to Instances.


.. cfy:node:: cloudify.gcp.nodes.Image

    A stored image which can be used as the base for newly created Instances.


.. cfy:node:: cloudify.gcp.nodes.KeyPair

    An SSH key-pair which will be uploaded to any Instances connected to it via
    ``cloudify.gcp.relationships.instance_connected_to_keypair``.

    Unlike other cloud providers,
    users are dynamically created on Instances based on the username specified by the uploaded SSH key,
    so the public key text must include a username in the comment section
    (keys generated using ``ssh-keygen`` have this by default).


.. cfy:node:: cloudify.gcp.nodes.InstanceGroup

    A GCP InstanceGroup.
    This is used to configure failover systems.
    InstanceGroups can be configured to scale automatically based on load,
    and will replace failing Instances with freashly started ones.


.. cfy:node:: cloudify.gcp.nodes.FirewallRule

    A GCP FirewallRule.
    This describes allowed traffic directed to either the whole of the specified network, or to Instances specified by matching tags.


.. cfy:node:: cloudify.gcp.nodes.SecurityGroup

    *Deprecated* please use a ``FirewallRule`` instead.

    A virtual SecurityGroup.
    Google Cloud Platform has no entity equivalent to a Security Group on AWS or OpenStack,
    so as a convenience Cloudify includes a virtual one.
    It is implemented behind the scenes using a specially constructed tag and a number of FirewallRules.


.. cfy:node:: cloudify.gcp.nodes.Route

    A defined route, which will be added to the specified network.
    If tags are specified, it will only be added to Instances matching them.


.. cfy:node:: cloudify.gcp.nodes.Network

    A GCP Network.
    This supports either auto-assigned or manual subnets.
    Legacy networks are not supported.
    See the GCP Manager and Networks section below if you plan to run a cloudify manager on GCP.


.. cfy:node:: cloudify.gcp.nodes.SubNetwork

    A GCP Subnetwork.
    Must be connected to a Network using ``cloudify.gcp.relationships.contained_in_network``.

    Only networks with the ``auto_subnets`` property disabled can be used.


.. cfy:node:: cloudify.gcp.nodes.GlobalAddress

    A GCP GlobalAddress.

    GlobalAddress can only be used together with GlobalForwardingRule. If you want to connect a static IP to an Instance, use StaticIP instead.


.. cfy:node:: cloudify.gcp.nodes.StaticIP

    *Deprecated* alias for ``GlobalAddress``


.. cfy:node:: cloudify.gcp.nodes.BackendService

    A group of Instances (contained within InstanceGroups) which can be used
    as the backend for load balancing.


.. cfy:node:: cloudify.gcp.nodes.UrlMap

    Maps URLs to BackendServices


.. cfy:node:: cloudify.gcp.nodes.GlobalForwardingRule

    A GCP GlobalForwardingRule.

    Can only be used in conjunction with a GlobalAddress to set up HTTP and HTTPS forwarding.


.. cfy:node:: cloudify.gcp.nodes.TargetProxy

    A TargetHttpProxy or TargetHttpsProxy.

    Specify which using the ``target_proxy_type`` property.


.. cfy:node:: cloudify.gcp.nodes.SslCertificate

    A TLS/SSL certificate and key. This will be used by a HTTPS TargetProxy to provide authenticated encryption for connecting users.


.. cfy:node:: cloudify.gcp.nodes.HealthCheck

    A GCP HealthCheck.

    This describes a method that a TargetProxy can use to verify that particualr backend Instances are functioning. Backends which fail the health check verification will be removed from the list of candidates.



DNS
---

.. cfy:node:: cloudify.gcp.nodes.DNSZone

    A Cloud DNS zone.
    Represents a particular DNS domain which you wish to manage through Google Cloud DNS.
    DNS nameservers can vary between different DNSZones. In order to find the correct nameserver entries for your domain, use the ``nameServers`` attribute from the created zone.


.. cfy:node:: cloudify.gcp.nodes.DNSRecord

    Corresponds to a particular subdomain (or `@` for the root) and record-type in the containing DNSZone.

    e.g. the ``A`` record for ``special_service.getcloudify.org``

    A number of convenience types are provided which update the default type (see DNSAAAARecord, DNSMXRecord, DNSTXTRecord, DNSNSRecord)


.. cfy:node:: cloudify.gcp.nodes.DNSAAAARecord


.. cfy:node:: cloudify.gcp.nodes.DNSMXRecord


.. cfy:node:: cloudify.gcp.nodes.DNSTXTRecord


.. cfy:node:: cloudify.gcp.nodes.DNSNSRecord




Relationships
=============


.. cfy:rel:: cloudify.gcp.relationships.instance_connected_to_security_group


.. cfy:rel:: cloudify.gcp.relationships.instance_connected_to_instance_group


.. cfy:rel:: cloudify.gcp.relationships.instance_connected_to_keypair


.. cfy:rel:: cloudify.gcp.relationships.dns_record_contained_in_zone


.. cfy:rel:: cloudify.gcp.relationships.dns_record_connected_to_ip


.. cfy:rel:: cloudify.gcp.relationships.instance_connected_to_ip


.. cfy:rel:: cloudify.gcp.relationships.instance_connected_to_disk


.. cfy:rel:: cloudify.gcp.relationships.forwarding_rule_connected_to_target_proxy


.. cfy:rel:: cloudify.gcp.relationships.contained_in_compute


.. cfy:rel:: cloudify.gcp.relationships.contained_in_network


.. cfy:rel:: cloudify.gcp.relationships.uses_as_backend


.. cfy:rel:: cloudify.gcp.relationships.dns_record_connected_to_instance


.. cfy:rel:: cloudify.gcp.relationships.instance_contained_in_network


