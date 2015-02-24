[![Latest Version](https://pypip.in/version/sodapy/badge.svg)](https://pypi.python.org/pypi/sodapy/)

# sodapy
Python bindings for the Socrata Open Data API

## Installation
You can install with `pip install sodapy`.

If you want to install from source, then `python setup.py install`.

## Requirements

This wrapper could be written using only the standard library. For ease of development, I've opted for a few useful packages.

- [Py](http://pylib.readthedocs.org/en/latest/)
- [Pytest](http://pytest.org/latest/)
- [Requests](http://docs.python-requests.org/en/latest/)

## Documentation

The [official Socrata API docs](http://dev.socrata.com/) provide thorough documentation of the available methods, as well as other client libraries. A quick list of eligible domains to use with the API is available [here](https://opendata.socrata.com/dataset/Socrata-Customer-Spotlights/6wk3-4ija).

## Examples

Retrieving data is easy! Use SQL-style keyword args to filter data, or lookup an individual row by simply appending the row identifier to the resource endpoint for that dataset.

    >>> from sodapy import Socrata
    >>> client = Socrata("sandbox.demo.socrata.com", "FakeAppToken", username="fakeuser@somedomain.com", password="ndKS92mS01msjJKs")

    >>> client.get("/resource/nimj-3ivp.json", limit=2)
	[{u'geolocation': {u'latitude': u'41.1085', u'needs_recoding': False, u'longitude': u'-117.6135'}, u'version': u'9', u'source': u'nn', u'region': u'Nevada', u'occurred_at': u'2012-09-14T22:38:01', u'number_of_stations': u'15', u'depth': u'7.60', u'magnitude': u'2.7', u'earthquake_id': u'00388610'}, {u'geolocation': {u'latitude': u'34.525', u'needs_recoding': False, u'longitude': u'-118.1527'}, u'version': u'0', u'source': u'ci', u'region': u'Southern California', u'occurred_at': u'2012-09-14T22:14:45', u'number_of_stations': u'35', u'depth': u'10.60', u'magnitude': u'1.5', u'earthquake_id': u'15215753'}]

	>>> client.get("/resource/nimj-3ivp.json", where="depth > 300", order="magnitude DESC", exclude_system_fields=False)
	[{u'geolocation': {u'latitude': u'-15.563', u'needs_recoding': False, u'longitude': u'-175.6104'}, u'version': u'9', u':updated_at': 1348778988, u'number_of_stations': u'275', u'region': u'Tonga', u':created_meta': u'21484', u'occurred_at': u'2012-09-13T21:16:43', u':id': 132, u'source': u'us', u'depth': u'328.30', u'magnitude': u'4.8', u':meta': u'{\n}', u':updated_meta': u'21484', u'earthquake_id': u'c000cnb5', u':created_at': 1348778988}, {u'geolocation': {u'latitude': u'-23.5123', u'needs_recoding': False, u'longitude': u'-179.1089'}, u'version': u'3', u':updated_at': 1348778988, u'number_of_stations': u'93', u'region': u'south of the Fiji Islands', u':created_meta': u'21484', u'occurred_at': u'2012-09-14T16:14:58', u':id': 32, u'source': u'us', u'depth': u'387.00', u'magnitude': u'4.6', u':meta': u'{\n}', u':updated_meta': u'21484', u'earthquake_id': u'c000cp1z', u':created_at': 1348778988}, {u'geolocation': {u'latitude': u'21.6711', u'needs_recoding': False, u'longitude': u'142.9236'}, u'version': u'C', u':updated_at': 1348778988, u'number_of_stations': u'136', u'region': u'Mariana Islands region', u':created_meta': u'21484', u'occurred_at': u'2012-09-13T11:19:07', u':id': 193, u'source': u'us', u'depth': u'300.70', u'magnitude': u'4.4', u':meta': u'{\n}', u':updated_meta': u'21484', u'earthquake_id': u'c000cmsq', u':created_at': 1348778988}]

    >>> client.get("/resource/nimj-3ivp/193.json", exclude_system_fields=False)
    {u'geolocation': {u'latitude': u'21.6711', u'needs_recoding': False, u'longitude': u'142.9236'}, u'version': u'C', u':updated_at': 1348778988, u'number_of_stations': u'136', u'region': u'Mariana Islands region', u':created_meta': u'21484', u'occurred_at': u'2012-09-13T11:19:07', u':id': 193, u'source': u'us', u'depth': u'300.70', u'magnitude': u'4.4', u':meta': u'{\n}', u':updated_meta': u'21484', u':position': 193, u'earthquake_id': u'c000cmsq', u':created_at': 1348778988}	

Create a new row in an existing dataset

    >>> data = [{'Delegation': 'AJU', 'Name': 'Alaska', 'Key': 'AL', 'Entity': 'Juneau'}]
    >>> client.upsert("/resource/eb9n-hr43.json", data)
	{u'Errors': 0, u'Rows Deleted': 0, u'Rows Updated': 0, u'By SID': 0, u'Rows Created': 1, u'By RowIdentifier': 0}

Update/Delete rows in a dataset.

    >>> data = [{'Delegation': 'sfa', ':id': 8, 'Name': 'bar', 'Key': 'doo', 'Entity': 'dsfsd'}, {':id': 7, ':deleted': True}]
	>>> client.upsert("/resource/eb9n-hr43.json", data)
	{u'Errors': 0, u'Rows Deleted': 1, u'Rows Updated': 1, u'By SID': 2, u'Rows Created': 0, u'By RowIdentifier': 0}

Upserts can even be performed with a csv file.

	>>> data = open("upsert_test.csv")
	>>> client.upsert("/resource/eb9n-hr43.json", data)
	{u'Errors': 0, u'Rows Deleted': 0, u'Rows Updated': 1, u'By SID': 1, u'Rows Created': 0, u'By RowIdentifier': 0}

The same is true for full replace.

	>>> data = open("replace_test.csv")
	>>> client.replace("/resource/eb9n-hr43.json", data)
	{u'Errors': 0, u'Rows Deleted': 0, u'Rows Updated': 0, u'By SID': 0, u'Rows Created': 12, u'By RowIdentifier': 0}

Delete an individual row.

	>>> client.delete("/resource/nimj-3ivp.json", id=2)
	<Response [200]>

Delete the entire dataset.

	>>> client.delete("/resource/nimj-3ivp.json")
	<Response [200]>

Wrap up when you're finished.

	>>> client.close()

## TODO and known issues
- Currently, the client does not support dataset creation.
- Tests are lacking.
