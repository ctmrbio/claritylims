import os
import yaml
import pytest
from clarity_ext_scripts.covid.sminet_client import (create_covid_request, SampleInfo,
                                                     ReferringClinic, Patient, Doctor,
                                                     SmiNetClient)


def not_setup_on_this_server():
    pytest.xfail(
        "This test requires sminet to be setup in your clarity-ext config")


def get_sminet_client():
    path = os.path.expanduser("~/.config/clarity-ext/clarity-ext.config")
    if not os.path.exists(path):
        not_setup_on_this_server()

    with open(path) as f:
        client_config = yaml.safe_load(f)

    if not "sminet_url" in client_config:
        not_setup_on_this_server()
    return SmiNetClient.SmiNetClientFromConfig(client_config)


def test_can_connect():
    """
    NOTE: We work against a whitelist on a jump server. Information available from team lead.
    NOTE: Reads config from your clarity-ext config which should point to the test environment.
          If sminet config is not available, the test is ignored. This is because the test
          can't run on the build server because it's not whitelisted at the moment.
    """

    client = get_sminet_client()
    #client.create()
