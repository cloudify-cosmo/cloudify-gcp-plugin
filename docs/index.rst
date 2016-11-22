.. cloudify-gcp-plugin documentation master file, created by
   sphinx-quickstart on Tue Nov  8 14:02:23 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

cloudify-gcp-plugin documentation
=================================
The Cloudify GCP plugin allows users to Cloudify to manage resources on `Google Cloud Platform`_.
See :ref:`node_types` for the supported resource types.

.. _Google Cloud Platform: https://cloud.google.com


test :cfy:node:`cloudify.gcp.nodes.Instance`

Contents:

.. toctree::
    :maxdepth: 2

    types
    manager

Plugin Requirements
-------------------

* Python versions:
  * 2.7.x
* `GCP <https://cloud.google.com/>`_ account


Compatibility
-------------

The GCP plugin uses the official `Google API Python Client <https://github.com/google/google-api-python-client>`_.


.. _account-info:

Account Information
-------------------

The plugin needs access to your GCP auth credentials (via the :ref:`gcp_config <common-properties>` parameter) in order to operate (but see :ref:`manager-config` if using a manager).



Terminology
-----------

* ``region`` refers to a general geographical area, such as "Central Europe" or "East US".
* ``zone`` refers to a distinct area within a region. Zones are usually referred to as '{region}-{zone}, i.e. 'us-east1-b' is a zone within the reigon 'us-east1'.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

