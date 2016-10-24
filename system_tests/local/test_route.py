########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCPRouteTest(GCPTest, TestCase):
    blueprint_name = 'route/simple-blueprint.yaml'

    inputs = (
            'project',
            'gcp_auth',
            )

    def assertions(self):
        def getter(x):
            return self.test_env.storage.get_node_instances(x)[0]

        routes = {
                'gateway_hop': getter('route_gateway_hop'),
                'not_connected': getter('route_not_connected'),
                'instance_hop': getter('route_instance_hop'),
                'ip_hop': getter('route_ip_hop'),
                }

        for route in routes.values():
            # We don't set the `kind` explicitly in the request so if it's in
            # `runtime_properties` that asserts we got a reasonable resource
            # response from the API.
            self.assertEqual(
                    'compute#route',
                    route['runtime_properties']['kind'])
