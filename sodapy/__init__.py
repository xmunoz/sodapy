from __future__ import print_function, absolute_import
from future import standard_library

standard_library.install_aliases()

from builtins import object
from io import StringIO
import requests
import csv
import json
import re
import os

from .constants import DEFAULT_API_PREFIX, OLD_API_PREFIX


class Socrata(object):
    '''
    The main class that interacts with the SODA API. Sample usage:
        from sodapy import Socrata
        client = Socrata("opendata.socrata.com", None)
    '''
    def __init__(self, domain, app_token, username=None, password=None,
                 access_token=None, session_adapter=None, timeout=10):
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

        authentication_validation(username, password, access_token)

        # use either basic HTTP auth or OAuth2.0
        if username and password:
            self.session.auth = (username, password)
        elif access_token:
            self.session.headers.update(
                {"Authorization": "OAuth {0}".format(access_token)}
            )

        if session_adapter:
            self.session.mount(session_adapter["prefix"],
                               session_adapter["adapter"])
            self.uri_prefix = session_adapter["prefix"]
        else:
            self.uri_prefix = "https://"

        if not isinstance(timeout, (int, float)):
            raise TypeError("Timeout must be numeric.")
        self.timeout = timeout

    def create(self, name, **kwargs):
        '''
        Create a dataset, including the field types. Optionally, specify args such as:
            description : description of the dataset
            columns : list of columns (see docs/tests for list structure)
            category : must exist in /admin/metadata
            tags : list of tag strings
            row_identifier : field name of primary key
            new_backend : whether to create the dataset in the new backend

        WARNING: This api endpoint might be deprecated.
        '''
        new_backend = kwargs.pop("new_backend", False)
        resource = _format_old_api_request(content_type="json")
        if new_backend:
            resource += "?nbe=true"

        payload = {"name": name}

        if "row_identifier" in kwargs:
            payload["metadata"] = {
                "rowIdentifier": kwargs.pop("row_identifier", None)
            }

        payload.update(kwargs)
        payload = _clear_empty_values(payload)

        return self._perform_update("post", resource, payload)

    def set_permission(self, dataset_identifier, permission="private", content_type="json"):
        '''
        Set a dataset's permissions to private or public
        Options are private, public

        '''
        resource = _format_old_api_request(dataid=dataset_identifier, content_type=content_type)

        params = {
            "method": "setPermission",
            "value": "public.read" if permission == "public" else permission
        }

        return self._perform_request("put", resource, params=params)

    def get_metadata(self, dataset_identifier, content_type="json"):
        '''
        Retrieve the metadata for a particular dataset.
        '''
        resource = _format_old_api_request(dataid=dataset_identifier, content_type=content_type)
        return self._perform_request("get", resource)

    def update_metadata(self, dataset_identifier, update_fields, content_type="json"):
        '''
        Update the metadata for a particular dataset.
            update_fields is a dictionary containing [metadata key:new value] pairs.

        This method performs a full replace for the key:value pairs listed in `update_fields`, and
        returns all of the metadata with the updates applied.
        '''
        resource = _format_old_api_request(dataid=dataset_identifier, content_type=content_type)
        return self._perform_update("put", resource, update_fields)

    def download_attachments(self, dataset_identifier, content_type="json",
                             download_dir="~/sodapy_downloads"):
        '''
        Download all of the attachments associated with a dataset.
        '''
        metadata = self.get_metadata(dataset_identifier, content_type=content_type)
        if "attachments" not in metadata['metadata']:
            print("No attachments were found or downloaded.")
            return

        attachments = metadata['metadata']['attachments']
        files = []

        download_dir = os.path.join(os.path.expanduser(download_dir), dataset_identifier)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        for attachment in attachments:
            file_path = os.path.join(download_dir, attachment["filename"])
            base = _format_old_api_request(dataid=dataset_identifier)
            resource = "{0}/files/{1}?download=true&filename={2}".format(base,
                                                                         attachment["assetId"],
                                                                         attachment["filename"])
            uri = "{0}{1}{2}".format(self.uri_prefix, self.domain, resource)
            _download_file(uri, file_path)
            files.append(file_path)

        print("The following files were downloaded:\n\t{0}".format("\n\t".join(files)))

    def publish(self, dataset_identifier, content_type="json"):
        '''
        The create() method creates a dataset in a "working copy" state.
        This method publishes it.
        '''
        base = _format_old_api_request(dataid=dataset_identifier)
        resource = "{0}/publication.{1}".format(base, content_type)

        return self._perform_request("post", resource)

    def get(self, dataset_identifier, content_type="json", **kwargs):
        '''
        Read data from the requested resource. Options for content_type are json,
        csv, and xml. Optionally, specify a keyword arg to filter results:

            select : the set of columns to be returned, defaults to *
            where : filters the rows to be returned, defaults to limit
            order : specifies the order of results
            group : column to group results on
            limit : max number of results to return, defaults to 1000
            offset : offset, used for paging. Defaults to 0
            q : performs a full text search for a value
            query : full SoQL query string, all as one parameter
            exclude_system_fields : defaults to true. If set to false, the
                response will include system fields (:id, :created_at, and
                :updated_at)

        More information about the SoQL parameters can be found at the official
        docs:
            http://dev.socrata.com/docs/queries.html

        More information about system fields can be found here:
            http://dev.socrata.com/docs/system-fields.html
        '''
        resource = _format_new_api_request(dataid=dataset_identifier, content_type=content_type)
        headers = _clear_empty_values({"Accept": kwargs.pop("format", None)})

        # SoQL parameters
        params = {
            "$select": kwargs.pop("select", None),
            "$where": kwargs.pop("where", None),
            "$order": kwargs.pop("order", None),
            "$group": kwargs.pop("group", None),
            "$limit": kwargs.pop("limit", None),
            "$offset": kwargs.pop("offset", None),
            "$q": kwargs.pop("q", None),
            "$query": kwargs.pop("query", None),
            "$$exclude_system_fields": kwargs.pop("exclude_system_fields",
                                                  None)
        }

        # Additional parameters, such as field names
        params.update(kwargs)
        params = _clear_empty_values(params)

        response = self._perform_request("get", resource, headers=headers,
                                         params=params)
        return response

    def upsert(self, dataset_identifier, payload, content_type="json"):
        '''
        Insert, update or delete data to/from an existing dataset. Currently
        supports json and csv file objects. See here for the upsert
        documentation:
            http://dev.socrata.com/publishers/upsert.html
        '''
        resource = _format_new_api_request(dataid=dataset_identifier, content_type=content_type)

        return self._perform_update("post", resource, payload)

    def replace(self, dataset_identifier, payload, content_type="json"):
        '''
        Same logic as upsert, but overwrites existing data with the payload
        using PUT instead of POST.
        '''
        resource = _format_new_api_request(dataid=dataset_identifier, content_type=content_type)

        return self._perform_update("put", resource, payload)

    def create_non_data_file(self, params, file_data):
        '''
        Creates a new file-based dataset with the name provided in the files
        tuple.  A valid file input would be:
        files = (
            {'file': ("gtfs2", open('myfile.zip', 'rb'))}
        )
        '''
        api_prefix = '/api/imports2/'

        if not params.get('method', None):
            params['method'] = 'blob'

        return self._perform_request("post", api_prefix, params=params, files=file_data)

    def replace_non_data_file(self, dataset_identifier, params, file_data):
        '''
        Same as create_non_data_file, but replaces a file that already exists in a
        file-based dataset.

        WARNING: a table-based dataset cannot be replaced by a file-based dataset.
                 Use create_non_data_file in order to replace.
        '''
        resource = _format_old_api_request(dataid=dataset_identifier, content_type="txt")

        if not params.get('method', None):
            params['method'] = 'replaceBlob'

        params['id'] = dataset_identifier

        return self._perform_request("post", resource, params=params, files=file_data)

    def _perform_update(self, method, resource, payload):
        '''
        Execute the update task.
        '''
        if isinstance(payload, (dict, list)):
            response = self._perform_request(method, resource,
                                             data=json.dumps(payload))
        elif isinstance(payload, file):
            headers = {
                "content-type": "text/csv",
            }
            response = self._perform_request(method, resource, data=payload,
                                             headers=headers)
        else:
            raise Exception("Unrecognized payload {0}. Currently only list-, dictionary-,"
                            " and file-types are supported.".format(type(payload)))

        return response

    def delete(self, dataset_identifier, row_id=None, content_type="json"):
        '''
        Delete the entire dataset, e.g.
            client.delete("nimj-3ivp")
        or a single row, e.g.
            client.delete("nimj-3ivp", row_id=4)
        '''
        if row_id:
            resource = _format_new_api_request(dataid=dataset_identifier, rowid=row_id,
                                               content_type=content_type)
        else:
            resource = _format_old_api_request(dataid=dataset_identifier,
                                               content_type=content_type)

        return self._perform_request("delete", resource)

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
        kwargs["timeout"] = self.timeout

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
        elif re.match(r'text\/plain;\s*charset=utf-8', content_type):
            try:
                return json.loads(response.text)
            except ValueError:
                return response.text
        else:
            raise Exception("Unknown response format: {0}"
                            .format(content_type))

    def close(self):
        '''
        Close the session.
        '''
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
    '''
    Scrap junk data from a dict.
    '''
    result = {}
    for param in args:
        if args[param] is not None:
            result[param] = args[param]
    return result


def _format_old_api_request(dataid=None, content_type=None):

    if dataid is not None:
        if content_type is not None:
            return "{0}/{1}.{2}".format(OLD_API_PREFIX, dataid, content_type)
        else:
            return "{0}/{1}".format(OLD_API_PREFIX, dataid)
    else:
        if content_type is not None:
            return "{0}.{1}".format(OLD_API_PREFIX, content_type)
        else:
            raise Exception("This method requires at least a dataset_id or content_type.")


def _format_new_api_request(dataid=None, row_id=None, content_type=None):
    if dataid is not None:
        if content_type is not None:
            if row_id is not None:
                return "{0}{1}/{2}.{3}".format(DEFAULT_API_PREFIX, dataid, row_id, content_type)
            else:
                return "{0}{1}.{2}".format(DEFAULT_API_PREFIX, dataid, content_type)

    raise Exception("This method requires at least a dataset_id or content_type.")


def authentication_validation(username, password, access_token):
    '''
    Only accept one form of authentication.
    '''
    if bool(username) is not bool(password):
        raise Exception("Basic authentication requires a username AND"
                        " password.")
    if (username and access_token) or (password and access_token):
        raise Exception("Cannot use both Basic Authentication and"
                        " OAuth2.0. Please use only one authentication"
                        " method.")


def _download_file(url, local_filename):
    '''
    Utility function that downloads a chunked response from the specified url to a local path.
    This method is suitable for larger downloads.
    '''
    response = requests.get(url, stream=True)
    with open(local_filename, 'wb') as outfile:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                outfile.write(chunk)
