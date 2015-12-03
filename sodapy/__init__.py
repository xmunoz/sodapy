from constants import MAX_LIMIT
from version import __version__, version_info

import requests
from cStringIO import StringIO
import csv
import json
import re

__author__ = "Cristina Munoz <hi@xmunoz.com>"


class Socrata(object):
    def __init__(self, domain, app_token, username=None, password=None,
                 access_token=None, session_adapter=None):
        '''
        The required arguments are:
            domain: the domain you wish you to access
            app_token: your Socrata application token
        Simple requests are possible without an app_token, though these
        requests will be rate-limited.

        For write/update/delete operations or private datasets, the Socrata API
        currently supports basic HTTP authentication, which requires these
        additional parameters.
            username: your Socrata username
            password: your Socrata password

        The basic HTTP authentication comes with a deprecation warning, and the
        current recommended authentication method is OAuth 2.0. To make
        requests on behalf of the user using OAuth 2.0 authentication, follow
        the recommended procedure and provide the final access_token to the
        client.

        More information about authentication can be found in the official
        docs:
            http://dev.socrata.com/docs/authentication.html
        '''
        if not domain:
            raise Exception("A domain is required.")
        self.domain = domain

        # set up the session with proper authentication crendentials
        self.session = requests.Session()
        if not app_token:
            print ("Warning: requests made without an app_token will be"
                   " subject to strict throttling limits.")
        else:
            self.session.headers.update({"X-App-token": app_token})

        self.authentication_validation(username, password, access_token)

        # use either basic HTTP auth or OAuth2.0
        if username and password:
            self.session.auth = (username, password)
        elif access_token:
            self.session.headers.update({"Authorization": "OAuth {0}"
                                        .format(access_token)})

        if session_adapter:
            self.session.mount(session_adapter["prefix"],
                               session_adapter["adapter"])
            self.uri_prefix = session_adapter["prefix"]
        else:
            self.uri_prefix = "https://"

    def authentication_validation(self, username, password, access_token):
        '''
        Only accept one form of authentication.
        '''
        if bool(username) != bool(password):
            raise Exception("Basic authentication requires a username AND"
                            " password.")
        if (username and access_token) or (password and access_token):
            raise Exception("Cannot use both Basic Authentication and"
                            " OAuth2.0. Please use only one authentication"
                            " method.")

    def create(self, name, **kwargs):
        '''
        Create a dataset, including the field types. Optionally, specify args such as:
            description : description of the dataset
            columns : list of columns (see docs/tests for list structure)
            category : must exist in /admin/metadata
            tags : array of tag strings
            row_identifier : field name of primary key
            new_backend : whether to create the dataset in the new backend
        '''
        new_backend = kwargs.pop("new_backend", False)
        resource = "/api/views.json" + ("?nbe=true" if new_backend else "")

        payload = {"name": name}

        if("row_identifier" in kwargs):
            payload["metadata"] = {
                "rowIdentifier": kwargs.pop("row_identifier", None)
            }

        payload.update(kwargs)
        payload = _clear_empty_values(payload)

        return self._perform_update("post", resource, payload)

    def set_permission(self, resource, permission="private"):
        '''
        Set a dataset's permissions to private or public
        Options are private, public
        '''
        params = {
            "method": "setPermission",
            "value": "public.read" if permission == "public" else permission
        }
        resource = resource.rsplit("/", 1)[-1] # just get the dataset id

        return self._perform_request("put", "/api/views/" + resource, params=params)

    def publish(self, resource):
        '''
        The create() method creates a dataset in a "working copy" state. 
        This method publishes it.
        '''
        resource = resource.rsplit("/", 1)[-1].split(".")[0] # just get the dataset id
        return self._perform_request("post", "/api/views/" + resource + "/publication.json")

    def get(self, resource, **kwargs):
        '''
        Read data from the requested resource. Optionally, specify a keyword
        arg to filter results:
            select : the set of columns to be returned, defaults to *
            where : filters the rows to be returned, defaults to limit
            order : specifies the order of results
            group : column to group results on
            limit : max number of results to return, defaults to 1000
            offset : offset, used for paging. Defaults to 0
            q : performs a full text search for a value
            exclude_system_fields : defaults to true. If set to false, the
                response will include system fields (:id, :created_at, and
                :updated_at)
        More information about the SoQL parameters can be found at the official
        docs:
            http://dev.socrata.com/docs/queries.html

        More information about system fields can be found here:
            http://dev.socrata.com/docs/system-fields.html
        '''
        headers = _clear_empty_values({"Accept": kwargs.pop("format", None)})

        params = {
            "$select": kwargs.pop("select", None),
            "$where": kwargs.pop("where", None),
            "$order": kwargs.pop("order", None),
            "$group": kwargs.pop("group", None),
            "$limit": kwargs.pop("limit", None),
            "$offset": kwargs.pop("offset", None),
            "$q": kwargs.pop("q", None),
            "$$exclude_system_fields": kwargs.pop("exclude_system_fields",
                                                  None)
        }

        params.update(kwargs)
        params = _clear_empty_values(params)

        if params.get("$limit") and params["$limit"] > MAX_LIMIT:
            raise Exception("Max limit exceeded! {0} is greater than the"
                            " Socrata API limit of {1}. More information on"
                            " the official API docs:"
                            " http://dev.socrata.com/docs/paging.html"
                            .format(params["$limit"], MAX_LIMIT))

        response = self._perform_request("get", resource, headers=headers,
                                         params=params)
        return response

    def upsert(self, resource, payload):
        '''
        Insert, update or delete data to/from an existing dataset. Currently
        supports json and csv file objects. See here for the upsert
        documentation:
            http://dev.socrata.com/publishers/upsert.html
        '''
        return self._perform_update("post", resource, payload)

    def replace(self, resource, payload):
        '''
        Same logic as upsert, but overwrites existing data with the payload
        using PUT instead of POST.
        '''
        return self._perform_update("put", resource, payload)

    def _perform_update(self, method, resource, payload):
        if isinstance(payload, list) or isinstance(payload, dict):
            response = self._perform_request(method, resource,
                                             data=json.dumps(payload))
        elif isinstance(payload, file):
            headers = {
                "content-type": "text/csv",
            }
            response = self._perform_request(method, resource, data=payload,
                                             headers=headers)
        else:
            raise Exception("Unrecognized payload {0}. Currently only lists"
                            " and files are supported.".format(type(payload)))

        return response

    def delete(self, resource, id=None):
        '''
        Delete the entire dataset, e.g.
            client.delete("/resource/nimj-3ivp.json")
        or a single row, e.g.
            client.delete("/resource/nimj-3ivp.json", id=4)
        '''
        if id:
            base, content_type = resource.rsplit(".", 1)
            delete_uri = "{0}/{1}.{2}".format(base, id, content_type)
        else:
            delete_uri = resource.replace("resource", "api/views")

        return self._perform_request("delete", delete_uri)

    def _perform_request(self, request_type, resource, **kwargs):
        '''
        Utility method that performs all requests.
        '''
        request_type_methods = set(["get", "post", "put", "delete"])
        if request_type not in request_type_methods:
            raise Exception("Unknown request type. Supported request types are"
                            ": {0}".format(", ".join(request_type_methods)))

        uri = "{0}{1}{2}".format(self.uri_prefix, self.domain, resource)

        # set a timeout, just to be safe
        kwargs["timeout"] = 10

        response = getattr(self.session, request_type)(uri, **kwargs)

        # handle errors
        if response.status_code not in (200, 202):
            _raise_for_status(response)

        # when responses have no content body (ie. delete, set_permission), 
        # simply return the whole response
        if not response.text:
            return response

        # for other request types, return most useful data
        content_type = response.headers.get('content-type').strip().lower()
        if re.match(r'application\/json;\s*charset=utf-8', content_type):
            return response.json()
        elif re.match(r'text\/csv;\s*charset=utf-8', content_type):
            csv_stream = StringIO(response.text)
            return [line for line in csv.reader(csv_stream)]
        elif re.match(r'application\/rdf\+xml;\s*charset=utf-8', content_type):
            return response.content
        else:
            raise Exception("Unknown response format: {0}"
                            .format(content_type))

    def close(self):
        self.session.close()


# helper methods
def _raise_for_status(response):
    '''
    Custom raise_for_status with more appropriate error message.
    '''
    http_error_msg = ""

    if 400 <= response.status_code < 500:
        http_error_msg = "{0} Client Error: {1}".format(response.status_code,
                                                        response.reason)

    elif 500 <= response.status_code < 600:
        http_error_msg = "{0} Server Error: {1}".format(response.status_code,
                                                        response.reason)

    if http_error_msg:
        try:
            more_info = response.json().get("message")
        except ValueError:
            more_info = None
        if more_info and more_info.lower() != response.reason.lower():
            http_error_msg += ".\n\t{0}".format(more_info)
        raise requests.exceptions.HTTPError(http_error_msg, response=response)


def _clear_empty_values(args):
    result = {}
    for param in args:
        if args[param] is not None:
            result[param] = args[param]
    return result
