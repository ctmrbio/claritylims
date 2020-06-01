from datetime import datetime
from clarity_ext_scripts.covid.services.sminet_service import SmiNetService
from clarity_ext_scripts.covid.services.knm_sminet_service import KNMSmiNetIntegrationService
from clarity_ext_scripts.covid.partner_api_client import KARLSSON_AND_NOVAK, ORG_URI_BY_NAME
from clarity_ext.cli import load_config
from clarity_ext_scripts.covid.services.knm_service import KNMSampleAccessor, KNMService
from sminet_client import SampleMaterial


"""
Tests the SmiNet/KNM integration
"""

config = load_config()


def test_can_create_request():
    """
    NOTE: We work against a whitelist on a jump server. Information available from team lead.
    NOTE: Reads config from your clarity-ext config which should point to the test environment.
          If sminet config is not available, the test is ignored. This is because the test
          can't run on the build server because it's not whitelisted at the moment.
    """

    constant_date = datetime(2020, 4, 30)
    knm_service = KNMService(config)
    sminet_service = SmiNetService(config)
    integration = KNMSmiNetIntegrationService(
        config, knm_service, sminet_service)
    org_uri = ORG_URI_BY_NAME[KARLSSON_AND_NOVAK]
    sample = KNMSampleAccessor(org_uri, "5236417647", constant_date, SampleMaterial.SVALG)
    sample_free_text = "Anamnes: Personalprov"

    lab_result = SmiNetService.create_scov2_positive_lab_result()
    integration.export_to_sminet(
        sample, "Lars Engstrand", lab_result, sample_free_text)
