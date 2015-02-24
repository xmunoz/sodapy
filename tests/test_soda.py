from sodapy import Socrata


def test_client():
    client = Socrata("something.com", "FakeAppToken")
    assert isinstance(client, Socrata)
