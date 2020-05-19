from datetime import datetime
from clarity_ext_scripts.covid.sminet_client import (create_covid_request, SampleInfo,
                                                     ReferringClinic, Patient, Doctor)
import lxml.etree as ET
mport os


def test_can_create_expected_request():
    constant_date = datetime(2020, 4, 30)
    request_created = datetime(2020, 5, 18, 18, 11, 6)

    sample_info = SampleInfo(status=1, sample_number=123, sample_date_arrival=constant_date,
                             sample_date_referral=constant_date, sample_material="Svalg",
                             sample_free_text_referral="Anamnes: Personalprov")
    clinic = ReferringClinic("Clinic name", "", "C", Doctor("Some doctor"))
    patient = Patient("1234", "k", "Some Name", 23)
    request = create_covid_request(
        sample_info, clinic, patient, request_created)

    fixtures = os.path.join(os.path.dirname(__file__), "fixtures")

    # For debug reasons one can uncomment this:
    # with open(os.path.join(fixtures, "sminet", "generated.xml"), "w") as fs:
    #     fs.write(request)

    with open(os.path.join(fixtures, "sminet", "valid_request.xml")) as fs:
        assert fs.read() == request
