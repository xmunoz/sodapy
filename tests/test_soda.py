from sodapy import Socrata
from sodapy.constants import DEFAULT_API_PREFIX
import requests
import requests_mock

import os.path
import inspect
import json


PREFIX = "https://"
DOMAIN = "fakedomain.com"
PATH = "songs"
APPTOKEN = "FakeAppToken"
USERNAME = "fakeuser"
PASSWORD = "fakepassword"
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(
        inspect.currentframe()))), "test_data")


def test_client():
    client = Socrata(DOMAIN, APPTOKEN)
    assert isinstance(client, Socrata)
    client.close()


def test_get():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, session_adapter=mock_adapter)

    response_data = "get_songs.txt"
    set_up_mock(adapter, "GET", response_data, 200)
    response = client.get(PATH)

    assert isinstance(response, list)
    assert len(response) == 10

    client.close()


def test_upsert_exception():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, session_adapter=mock_adapter)

    response_data = "403_response_json.txt"
    set_up_mock(adapter, "POST", response_data, 403, reason="Forbidden")

    data = [{"theme": "Surfing", "artist": "Wavves",
             "title": "King of the Beach", "year": "2010"}]
    try:
        response = client.upsert(PATH, data)
    except Exception, e:
        assert isinstance(e, requests.exceptions.HTTPError)
    else:
        raise AssertionError("No exception raised for bad request.")
    finally:
        client.close()


def test_upsert():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, username=USERNAME, password=PASSWORD,
                     session_adapter=mock_adapter)

    response_data = "upsert_songs.txt"
    data = [{"theme": "Surfing", "artist": "Wavves",
             "title": "King of the Beach", "year": "2010"}]
    set_up_mock(adapter, "POST", response_data, 200)
    response = client.upsert(PATH, data)

    assert isinstance(response, dict)
    assert response.get("Rows Created") == 1
    client.close()


def test_replace():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, username=USERNAME, password=PASSWORD,
                     session_adapter=mock_adapter)

    response_data = "replace_songs.txt"
    data = [
        {"theme": "Surfing", "artist": "Wavves", "title": "King of the Beach",
         "year": "2010"},
        {"theme": "History", "artist": "Best Friends Forever",
         "title": "Abe Lincoln", "year": "2008"},
    ]
    set_up_mock(adapter, "PUT", response_data, 200)
    response = client.replace(PATH, data)

    assert isinstance(response, dict)
    assert response.get("Rows Created") == 2
    client.close()


def test_delete():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, username=USERNAME, password=PASSWORD,
                     session_adapter=mock_adapter)

    uri = "{0}{1}{2}{3}.json".format(PREFIX, DOMAIN, "/api/views/", PATH)
    adapter.register_uri("DELETE", uri, status_code=200)
    response = client.delete(PATH)
    assert response.status_code == 200

    try:
        client.delete("foobar")
    except Exception, e:
        assert isinstance(e, requests_mock.exceptions.NoMockAddress)
    finally:
        client.close()
        
def test_create():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, username=USERNAME, password=PASSWORD,
                     session_adapter=mock_adapter)
    
    response_data = "create_foobar.txt"
    set_up_mock(adapter, "POST", response_data, 200, dataset_identifier=None)
    
    columns = [
        {"fieldName": "foo", "name": "Foo", "dataTypeName": "text"},
        {"fieldName": "bar", "name": "Bar", "dataTypeName": "number"}
    ]
    tags = ["foo", "bar"]
    response = client.create("Foo Bar", description="test dataset", 
                  columns=columns, tags=tags, row_identifier="bar")
    
    request = adapter.request_history[0]
    request_payload = json.loads(request.text) # can't figure out how to use .json
    
    # Test request payload
    for dataset_key in ["name", "description", "columns", "tags"]:
        assert dataset_key in request_payload

    for column_key in ["fieldName", "name", "dataTypeName"]:
        assert column_key in request_payload["columns"][0]
    
    # Test response
    assert isinstance(response, dict)
    assert len(response.get("id")) == 9
    client.close()

def test_set_permission():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, username=USERNAME, password=PASSWORD,
                     session_adapter=mock_adapter)

    response_data = "empty.txt"
    set_up_set_permissions_mock(adapter, "PUT", response_data, 200)
    
    # Test response
    response = client.set_permission(PATH, "public")
    assert response.status_code == 200
    
    # Test request
    request = adapter.request_history[0]
    qs = request.url.split("?")[-1]
    assert qs == "method=setPermission&value=public.read"
    client.close()
    
def test_publish():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, username=USERNAME, password=PASSWORD,
                     session_adapter=mock_adapter)
    
    response_data = "create_foobar.txt"
    set_up_publish_mock(adapter, "POST", response_data, 200)
    
    response = client.publish(PATH)
    assert isinstance(response, dict)
    assert len(response.get("id")) == 9
    client.close()

def set_up_publish_mock(adapter, method, response, response_code, reason="OK", auth=None,
                        dataset_identifier=PATH, content_type="json"):

    path = os.path.join(TEST_DATA_PATH, response)
    with open(path, "rb") as f:
        body = json.load(f)

    uri = "{0}{1}{2}{3}{4}{5}".format(PREFIX, DOMAIN, "/api/views/", dataset_identifier,
                                      "/publication.", content_type)

    headers = {
        "content-type": "application/json; charset=utf-8"
    }

    adapter.register_uri(method, uri, status_code=response_code, json=body, reason=reason,
                         headers=headers)

def set_up_set_permissions_mock(adapter, method, response, response_code, reason="OK", auth=None,
                                dataset_identifier=PATH, content_type="json"):

    path = os.path.join(TEST_DATA_PATH, response)
    with open(path, "rb") as f:
        try:
            body = json.load(f)
            raise AssertionError("This should fail because file should be empty.")
        except ValueError:
            body = None

    uri = "{0}{1}{2}{3}.{4}".format(PREFIX, DOMAIN, "/api/views/", dataset_identifier,
                                    content_type)

    headers = {
        "content-type": "application/json; charset=utf-8"
    }

    adapter.register_uri(method, uri, status_code=response_code, json=body, reason=reason,
                         headers=headers)

def set_up_mock(adapter, method, response, response_code, reason="OK", auth=None,
                dataset_identifier=PATH, content_type="json"):

    path = os.path.join(TEST_DATA_PATH, response)
    with open(path, "rb") as f:
        body = json.load(f)

    if dataset_identifier is None:  # for create endpoint
        uri = "{0}{1}{2}".format(PREFIX, DOMAIN, "/api/views.json")
    else: # mast cases
        uri = "{0}{1}{2}{3}.{4}".format(PREFIX, DOMAIN, DEFAULT_API_PREFIX, dataset_identifier, content_type)

    headers = {
        "content-type": "application/json; charset=utf-8"
    }
    adapter.register_uri(method, uri, status_code=response_code,
                         json=body, reason=reason, headers=headers)
