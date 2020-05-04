
import sys
import yaml
import logging


import click
from retry import retry
from requests import ConnectionError, Timeout

from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client, ServiceRequestAlreadyExists, \
    OrganizationReferralCodeNotFound, CouldNotCreateServiceRequest, PartnerClientAPIException, COVID_RESPONSE_FAILED, \
    MoreThanOneOrganizationReferralCodeFound

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


@click.group()
@click.option("--config")
@click.pass_context
def cli(ctx, config):
    with open(config) as f:
        client_config = yaml.safe_load(f)
    client = PartnerAPIV7Client(**client_config)
    ctx.obj['CLIENT'] = client


@cli.command()
@click.argument("filename")
@click.pass_context
def validate(ctx, filename):
    log.info("Validating...")
    client = ctx.obj["CLIENT"]

    barcodes = read_barcodes_from_file(filename)
    log.info("Found {} barcodes in file.".format(len(barcodes)))

    service_request_ids = []
    more_than_one_ref_found = []
    # Check if there already exists a service request
    for barcode in barcodes:
        try:
            service_request_id = search_for_service_request(client, barcode)
            service_request_ids.append(service_request_id)
        except OrganizationReferralCodeNotFound as e:
            pass
        except MoreThanOneOrganizationReferralCodeFound as e:
            more_than_one_ref_found.append(barcode)

    log.info("Found service requests for for {}/{} of the barcodes.".format(
        len(service_request_ids), len(barcodes)))
    log.info("There were multiple service requests for {} barcodes.".format(
        len(more_than_one_ref_found)))


# Since it will cause us a headache is we fail half way through reporting
# due to connection problems, retry this.
@retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
def send_results_to_partner(client, service_request_id):
    client.post_diagnosis_report(service_request_id=service_request_id,
                                 diagnosis_result=COVID_RESPONSE_FAILED,
                                 analysis_results=[{"value": -1}])


@retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
def create_anonymous_service_request(client, barcode):
    return client.create_anonymous_service_request(barcode)


@retry((ConnectionError, Timeout), tries=3, delay=2, backoff=2)
def search_for_service_request(client, barcode):
    search_found = client.search_for_service_request(
        org="http://uri.d-t.se/id/Identifier/i-referral-code", org_referral_code=barcode)
    service_request_id = search_found["resource"]["id"]
    return service_request_id


@cli.command()
@click.argument("filename")
@click.pass_context
def execute(ctx, filename):
    log.info("Executing...")

    client = ctx.obj["CLIENT"]

    barcodes = read_barcodes_from_file(filename)
    log.info("Found {} barcodes in file.".format(len(barcodes)))

    # Check if there already exists a service request
    for barcode in barcodes:
        try:
            service_request_id = search_for_service_request(client, barcode)
            log.info(("Found service request for barcode {}. Service request "
                      "id was: {}. Disregarding.").format(barcode,
                                                          service_request_id))
        except OrganizationReferralCodeNotFound as e:
            log.info(
                "Did not find service request for: {}. Will create a service request.".format(barcode))

            service_request_id = create_anonymous_service_request(
                client, barcode)

            log.info("Successfully created service request for barcode: {}. Got service request id: {}".format(
                barcode, service_request_id
            ))

            log.info("Will try to send failed result for barcode: {} with service_request_id: {}".format(
                barcode,
                service_request_id))
            send_results_to_partner(client, service_request_id)

            log.info("Successfully sent failed result for barcode: {} with service request id: {}".format(
                barcode,
                service_request_id))

    log.info(
        "Successfully sent failed results for all unregistered barcodes in file.")


def read_barcodes_from_file(filename):
    barcodes = []
    with open(filename) as f:
        for line in f:
            if "Referensnummer" in line:
                continue
            barcodes.append(line.split("\t")[0])

    log.info("Read {} barcodes from file".format(len(barcodes)))
    return barcodes


if __name__ == '__main__':
    cli(obj={})
