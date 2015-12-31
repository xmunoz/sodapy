[![PyPI version](https://badge.fury.io/py/sodapy.svg)](http://badge.fury.io/py/sodapy) [![Build Status](https://travis-ci.org/xmunoz/sodapy.svg?branch=master)](https://travis-ci.org/xmunoz/sodapy)

# sodapy
Python bindings for the Socrata Open Data API

## Installation
You can install with `pip install sodapy`.

If you want to install from source, then `python setup.py install`.

## Requirements

At it's core, this library depends heavily on the [Requests](http://docs.python-requests.org/en/latest/) package. All other requirements can be found in (requirements.txt](https://github.com/xmunoz/sodapy/blob/master/requirements.txt).

## Documentation

The [official Socrata API docs](http://dev.socrata.com/) provide thorough documentation of the available methods, as well as other client libraries. A quick list of eligible domains to use with the API is available [here](https://opendata.socrata.com/dataset/Socrata-Customer-Spotlights/6wk3-4ija).

## Interface

### Table of Contents

    - [client](#client)
    - [`get`](#get)
    - [`get_metadata`](#get_metadata)
    - [`download_attachments`](#download_attachments)
    - [`create`](#create)
    - [`publish`](#publish)
    - [`set_permission`](#set_permission)
    - [`upsert`](#upsert)
    - [`replace`](#replace)
    - [`delete`](#delete)
    - [`close`](#close)

### client

Import the library and set up a connection to get started.

    >>> from sodapy import Socrata
    >>> client = Socrata("sandbox.demo.socrata.com", "FakeAppToken", username="fakeuser@somedomain.com", password="ndKS92mS01msjJKs")

`username` and `password` are only required for creating or modifying data. An application token isn't strictly required (can be `None`), but queries executed from a client without an application token will be sujected to strict throttling limits.

### `get`

Retrieve data from the requested resources. Filter and query data by field name, id, or using [SoQL keywords](https://dev.socrata.com/docs/queries/).

    >>> client.get("nimj-3ivp", limit=2)
	[{u'geolocation': {u'latitude': u'41.1085', u'needs_recoding': False, u'longitude': u'-117.6135'}, u'version': u'9', u'source': u'nn', u'region': u'Nevada', u'occurred_at': u'2012-09-14T22:38:01', u'number_of_stations': u'15', u'depth': u'7.60', u'magnitude': u'2.7', u'earthquake_id': u'00388610'}, {...}]

	>>> client.get("nimj-3ivp", where="depth > 300", order="magnitude DESC", exclude_system_fields=False)
	[{u'geolocation': {u'latitude': u'-15.563', u'needs_recoding': False, u'longitude': u'-175.6104'}, u'version': u'9', u':updated_at': 1348778988, u'number_of_stations': u'275', u'region': u'Tonga', u':created_meta': u'21484', u'occurred_at': u'2012-09-13T21:16:43', u':id': 132, u'source': u'us', u'depth': u'328.30', u'magnitude': u'4.8', u':meta': u'{\n}', u':updated_meta': u'21484', u'earthquake_id': u'c000cnb5', u':created_at': 1348778988}, {...}]

    >>> client.get("nimj-3ivp/193", exclude_system_fields=False)
    {u'geolocation': {u'latitude': u'21.6711', u'needs_recoding': False, u'longitude': u'142.9236'}, u'version': u'C', u':updated_at': 1348778988, u'number_of_stations': u'136', u'region': u'Mariana Islands region', u':created_meta': u'21484', u'occurred_at': u'2012-09-13T11:19:07', u':id': 193, u'source': u'us', u'depth': u'300.70', u'magnitude': u'4.4', u':meta': u'{\n}', u':updated_meta': u'21484', u':position': 193, u'earthquake_id': u'c000cmsq', u':created_at': 1348778988}

    >>> client.get("nimj-3ivp", region="Kansas")
	[{u'geolocation': {u'latitude': u'38.10', u'needs_recoding': False, u'longitude': u'-100.6135'}, u'version': u'9', u'source': u'nn', u'region': u'Kansas', u'occurred_at': u'2010-09-19T20:52:09', u'number_of_stations': u'15', u'depth': u'300.0', u'magnitude': u'1.9', u'earthquake_id': u'00189621'}, {...}]

### `get_metadata`

Retrieve the metadata associated with a particular dataset.

    >>> client.get_metadata("nimj-3ivp")
    {"newBackend": false, "licenseId": "CC0_10", "publicationDate": 1436655117, "viewLastModified": 1451289003, "owner": {"roleName": "administrator", "rights": [], "displayName": "Brett", "id": "cdqe-xcn5", "screenName": "Brett"}, "query": {}, "id": "songs", "createdAt": 1398014181, "category": "Public Safety", "publicationAppendEnabled": true, "publicationStage": "published", "rowsUpdatedBy": "cdqe-xcn5", "publicationGroup": 1552205, "displayType": "table", "state": "normal", "attributionLink": "http://foo.bar.com", "tableId": 3523378, "columns": [], "metadata": {"rdfSubject": "0", "renderTypeConfig": {"visible": {"table": true}}, "availableDisplayTypes": ["table", "fatrow", "page"], "attachments": ... }}

### `download_attachments`

Download all attachments associated with a dataset.

    >>> client.download_attachments("nimj-3ivp", download_dir="~/Desktop")
    The following files were downloaded:
        /Users/xmunoz/Desktop/nimj-3ivp/FireIncident_Codes.PDF
        /Users/xmunoz/Desktop/nimj-3ivp/AccidentReport.jpg

The default download path is `~/sodapy_downloads`.

### `create`

Create a new dataset.

	>>> columns = [{"fieldName": "delegation", "name": "Delegation", "dataTypeName": "text"}, {"fieldName": "members", "name": "Members", "dataTypeName": "number"}]
	>>> tags = ["politics", "geography"]
	>>> client.create("Delegates", description="List of delegates", columns=columns, row_identifier="delegation", tags=tags, category="Transparency")
	{u'id': u'2frc-hyvj', u'name': u'Foo Bar', u'description': u'test dataset', u'publicationStage': u'unpublished', u'columns': [ { u'name': u'Foo', u'dataTypeName': u'text', u'fieldName': u'foo', ... }, { u'name': u'Bar', u'dataTypeName': u'number', u'fieldName': u'bar', ... } ], u'metadata': { u'rowIdentifier': 230641051 }, ... }

### `publish`

Publish a dataset after creating it, i.e. take it out of 'working copy' mode. The dataset id `id` returned from `create` will be used to publish.

	>>> client.publish("2frc-hyvj")
	{u'id': u'2frc-hyvj', u'name': u'Foo Bar', u'description': u'test dataset', u'publicationStage': u'unpublished', u'columns': [ { u'name': u'Foo', u'dataTypeName': u'text', u'fieldName': u'foo', ... }, { u'name': u'Bar', u'dataTypeName': u'number', u'fieldName': u'bar', ... } ], u'metadata': { u'rowIdentifier': 230641051 }, ... }

### `set_permission`

Set the permissions of a dataset to public or private.

	>>> client.set_permission("2frc-hyvj", "public")
	<Response [200]>

### `upsert`

Create a new row in an existing dataset.

    >>> data = [{'Delegation': 'AJU', 'Name': 'Alaska', 'Key': 'AL', 'Entity': 'Juneau'}]
    >>> client.upsert("eb9n-hr43", data)
	{u'Errors': 0, u'Rows Deleted': 0, u'Rows Updated': 0, u'By SID': 0, u'Rows Created': 1, u'By RowIdentifier': 0}

Update/Delete rows in a dataset.

    >>> data = [{'Delegation': 'sfa', ':id': 8, 'Name': 'bar', 'Key': 'doo', 'Entity': 'dsfsd'}, {':id': 7, ':deleted': True}]
	>>> client.upsert("eb9n-hr43", data)
	{u'Errors': 0, u'Rows Deleted': 1, u'Rows Updated': 1, u'By SID': 2, u'Rows Created': 0, u'By RowIdentifier': 0}

`upsert`'s can even be performed with a csv file.

	>>> data = open("upsert_test.csv")
	>>> client.upsert("eb9n-hr43", data)
	{u'Errors': 0, u'Rows Deleted': 0, u'Rows Updated': 1, u'By SID': 1, u'Rows Created': 0, u'By RowIdentifier': 0}

### `replace`

Similar in usage to `upsert`, but overwrites existing data.

	>>> data = open("replace_test.csv")
	>>> client.replace("eb9n-hr43", data)
	{u'Errors': 0, u'Rows Deleted': 0, u'Rows Updated': 0, u'By SID': 0, u'Rows Created': 12, u'By RowIdentifier': 0}

### `delete`

Delete an individual row.

	>>> client.delete("nimj-3ivp", id=2)
	<Response [200]>

Delete the entire dataset.

	>>> client.delete("nimj-3ivp")
	<Response [200]>


### `close`

Close the seesion when you're finished.

	>>> client.close()

## Run tests

    $ ./runtests tests/

## Contributing

See [CONTRIBUTING.md]().
