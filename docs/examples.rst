
Examples
========


DNS
---

This example shows how to set up a Cloud DNS zone
and how to connect the IP addresses from
:cfy:node:`cloudify.gcp.nodes.Instance`
and :cfy:node:`cloudify.gcp.nodes.Address`.

Excerpt from https://github.com/cloudify-cosmo/cloudify-gcp-plugin/blob/master/system_tests/resources/dns/simple-blueprint.yaml:

.. literalinclude:: ../system_tests/resources/dns/simple-blueprint.yaml
    :language: yaml
    :lines: 27-
    :lineno-match:

This will create a DNS zone with the following entries:

================    ====================================    =========
node                name                                    maps to
================    ====================================    =========
``test``            test.getcloudify.org                    ``instance``'s ``ip`` attribute
``direct-to-ip``    direct-to-ip.getcloudify.org            ``ip``'s  address
``name_2``          names-are-relative.getcloudify.org      127.3.4.5
``literal-only``    literal-only.getcloudify.org            10.9.8.7
================    ====================================    =========

An important thing to note here is that the zone's ``nameServers`` attribute
must be checked *after* creating the zone and the values provided must be
used to populate the domain name's nameserver entries
(the blueprint makes this visible as the ``nameservers`` output).

