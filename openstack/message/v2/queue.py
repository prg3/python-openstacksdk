# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from openstack.message import message_service
from openstack import resource2


class Queue(resource2.Resource):
    resources_key = "queues"
    base_path = "/queues"
    service = message_service.MessageService()

    # capabilities
    allow_create = True
    allow_list = True
    allow_get = True
    allow_delete = True

    # Properties
    #: The default TTL of messages defined for a queue, which will effect for
    #: any messages posted to the queue.
    default_message_ttl = resource2.Body("_default_message_ttl")
    #: Description of the queue.
    description = resource2.Body("description")
    #: The max post size of messages defined for a queue, which will effect
    #: for any messages posted to the queue.
    max_messages_post_size = resource2.Body("_max_messages_post_size")
    #: Name of the queue. The name is the unique identity of a queue. It
    #: must not exceed 64 bytes in length, and it is limited to US-ASCII
    #: letters, digits, underscores, and hyphens.
    name = resource2.Body("name", alternate_id=True)
    #: The ID to identify the client accessing Zaqar API. Must be specified
    #: in header for each API request.
    client_id = resource2.Header("Client-ID")
    #: The ID to identify the project accessing Zaqar API. Must be specified
    #: in case keystone auth is not enabled in Zaqar service.
    project_id = resource2.Header("X-PROJECT-ID")

    def create(self, session, prepend_key=True):
        request = self._prepare_request(requires_id=True,
                                        prepend_key=prepend_key)
        headers = {
            "Client-ID": self.client_id or str(uuid.uuid4()),
            "X-PROJECT-ID": self.project_id or session.get_project_id()
        }
        request.headers.update(headers)
        response = session.put(request.uri, endpoint_filter=self.service,
                               json=request.body, headers=request.headers)

        self._translate_response(response, has_body=False)
        return self

    @classmethod
    def list(cls, session, paginated=False, **params):
        """This method is a generator which yields queue objects.

        This is almost the copy of list method of resource2.Resource class.
        The only difference is the request header now includes `Client-ID`
        and `X-PROJECT-ID` fields which are required by Zaqar v2 API.
        """
        more_data = True
        query_params = cls._query_mapping._transpose(params)
        uri = cls.base_path % params
        headers = {
            "Client-ID": params.get('client_id', None) or str(uuid.uuid4()),
            "X-PROJECT-ID": params.get('project_id', None
                                       ) or session.get_project_id()
        }

        while more_data:
            resp = session.get(uri, endpoint_filter=cls.service,
                               headers=headers, params=query_params)
            resp = resp.json()
            resp = resp[cls.resources_key]

            if not resp:
                more_data = False

            yielded = 0
            new_marker = None
            for data in resp:
                value = cls.existing(**data)
                new_marker = value.id
                yielded += 1
                yield value

            if not paginated:
                return
            if "limit" in query_params and yielded < query_params["limit"]:
                return
            query_params["limit"] = yielded
            query_params["marker"] = new_marker

    def get(self, session, requires_id=True):
        request = self._prepare_request(requires_id=requires_id)
        headers = {
            "Client-ID": self.client_id or str(uuid.uuid4()),
            "X-PROJECT-ID": self.project_id or session.get_project_id()
        }
        request.headers.update(headers)
        response = session.get(request.uri, endpoint_filter=self.service,
                               headers=headers)
        self._translate_response(response)

        return self

    def delete(self, session):
        request = self._prepare_request()
        headers = {
            "Client-ID": self.client_id or str(uuid.uuid4()),
            "X-PROJECT-ID": self.project_id or session.get_project_id()
        }
        request.headers.update(headers)
        response = session.delete(request.uri, endpoint_filter=self.service,
                                  headers=headers)

        self._translate_response(response, has_body=False)
        return self
