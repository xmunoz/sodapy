from sodapy import Socrata
import requests
import requests_mock

import os.path
import inspect
import json


PREFIX = "http://"
DOMAIN = "fakedomain.com"
PATH = "/songs.json"
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

    path = "/songs.json"
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

    uri = "{0}{1}{2}".format(PREFIX, DOMAIN, PATH)
    adapter.register_uri("DELETE", uri, status_code=200)
    response = client.delete(PATH)
    assert response.status_code == 200

    try:
        client.delete("/foobar.json")
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
    resource = "/api/views.json"
    set_up_mock(adapter, "POST", response_data, 200, resource=resource)
    
    columns = [
        {"fieldName": "foo", "name": "Foo", "dataTypeName": "text"},
        {"fieldName": "bar", "name": "Bar", "dataTypeName": "number"}
    ]
    response = client.create("Foo Bar", description="test dataset", 
                  columns=columns, row_identifier="bar")
    
    request = adapter.request_history[0]
    request_payload = json.loads(request.text) # can't figure out how to use .json
    
    # Test request payload
    for dataset_key in ["name", "description", "columns"]:
        assert dataset_key in request_payload

    for column_key in ["fieldName", "name", "dataTypeName"]:
        assert column_key in request_payload["columns"][0]
    
    # Test response
    assert isinstance(response, dict)
    assert len(response.get("id")) == 9
    
    client.close()

def test_set_public():
    mock_adapter = {}
    mock_adapter["prefix"] = PREFIX
    adapter = requests_mock.Adapter()
    mock_adapter["adapter"] = adapter
    client = Socrata(DOMAIN, APPTOKEN, username=USERNAME, password=PASSWORD,
                     session_adapter=mock_adapter)

    response_data = "empty.txt"
    resource = "/api/views" + PATH
    set_up_mock(adapter, "PUT", response_data, 200, resource=resource)
    
    # Test response
    response = client.set_public(PATH)
    assert response.status_code == 200
    
    # Test request
    request = adapter.request_history[0]
    assert "method" in request.qs
    assert "value" in request.qs
    
    client.close()

def set_up_mock(adapter, method, response, response_code,
                reason="OK", auth=None, resource=PATH):
    path = os.path.join(TEST_DATA_PATH, response)
    with open(path, "rb") as f:
        try:
            body = json.load(f)
        except ValueError:
            body = None
            
    uri = "{0}{1}{2}".format(PREFIX, DOMAIN, resource)
    headers = {
        "content-type": "application/json; charset=utf-8"
    }
    adapter.register_uri(method, uri, status_code=response_code,
                         json=body, reason=reason, headers=headers)
