import os
from uuid import uuid4
import random
import string
import yaml
from datetime import datetime
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


def test_can_create_request():
    """
    NOTE: We work against a whitelist on a jump server. Information available from team lead.
    NOTE: Reads config from your clarity-ext config which should point to the test environment.
          If sminet config is not available, the test is ignored. This is because the test
          can't run on the build server because it's not whitelisted at the moment.
    """

    client = get_sminet_client()
    constant_date = datetime(2020, 4, 30)
    request_created = datetime(2020, 5, 18, 18, 11, 6)
    prefix = "int-tests-"
    rnd = "".join(random.choice(string.ascii_uppercase + string.digits)
                  for _ in range(25 - len(prefix)))
    sample_id = prefix + rnd
    sample_info = SampleInfo(status=1, sample_id=sample_id, sample_date_arrival=constant_date,
                             sample_date_referral=constant_date, sample_material="Svalg",
                             sample_free_text_referral="Anamnes: Personalprov")
    clinic = ReferringClinic("Clinic name", "", "C", Doctor("Some doctor"))
    patient = Patient("1234", "k", "Some Name", 23)
    client.create(sample_info, clinic, patient)
