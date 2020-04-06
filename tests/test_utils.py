import sodapy.utils as utils
import pytest
import requests


@pytest.mark.parametrize(
    ("status_code", "status_type", "reason", "raises_exception"),
    [
        (200, "Success", "OK", False),
        (300, "Redirection", "Multiple Choices", False),
        (400, "Client Error", "Bad Request", True),
        (500, "Server Error", "Internal Server Error", True),
        (600, "Foo Bar", "Here be dragons", False),
    ],
)
def test_raise_for_status(status_code, status_type, reason, raises_exception):
    response = requests.models.Response()
    response.status_code = status_code
    response.reason = reason

    if raises_exception:
        with pytest.raises(
            requests.exceptions.HTTPError,
            match="{} {}: {}".format(status_code, status_type, reason),
        ):
            utils.raise_for_status(response)
    else:
        utils.raise_for_status(response)
