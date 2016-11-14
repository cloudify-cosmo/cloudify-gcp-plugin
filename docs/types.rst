

Types
=====

Compute
-------

.. cfy:node:: cloudify.gcp.nodes.Instance

    here is the doc


.. cfy:node:: cloudify.gcp.nodes.InstanceGroup

    tadaa!


.. cfy:node:: cloudify.gcp.nodes.FirewallRule

    a wall of fire


DNS
---

.. cfy:node:: cloudify.gcp.nodes.DNSZone

    A Cloud DNS zone.

    Represents a particular DNS domain which you wish to manage through Google Cloud DNS.
    DNS nameservers can vary between different DNSZones. In order to find the correct nameserver entries for your domain, use the ``nameServers`` attribute from the created zone.


.. cfy:node:: cloudify.gcp.nodes.DNSRecord



Relationships
=============


.. cfy:rel:: cloudify.gcp.relationships.instance_connected_to_security_group

