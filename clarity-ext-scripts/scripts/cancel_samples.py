
import yaml

import click
import retry
from requests import ConnectionError, Timeout

from clarity_ext_scripts.covid.partner_api_client import PartnerAPIV7Client, ServiceRequestAlreadyExists, \
    OrganizationReferralCodeNotFound, CouldNotCreateServiceRequest, PartnerClientAPIException, COVID_RESPONSE_FAILED


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
    click.echo("Validating...")
    client = ctx.obj["CLIENT"]

    barcodes = read_barcodes_from_file(filename)
    click.echo("Found {} barcodes in file.".format(len(barcodes)))

    service_request_ids = []
    # Check if there already exists a service request
    for barcode in barcodes:
        try:
            search_found = client.search_for_service_request(
                org="http://uri.d-t.se/id/Identifier/i-referral-code", org_referral_code=barcode)
            service_request_id = search_found["resource"]["id"]
            service_request_ids.append(service_request_id)
        except OrganizationReferralCodeNotFound as e:
            pass

    click.echo("Found service requests for for {}/{} of the barcodes.".format(
        len(service_request_ids, len(barcodes))))


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


@cli.command()
@click.argument("filename")
@click.pass_context
def execute(ctx, filename):
    click.echo("Executing...")

    client = ctx.obj["CLIENT"]

    barcodes = read_barcodes_from_file(filename)
    click.echo("Found {} barcodes in file.".format(len(barcodes)))

    service_request_ids = []
    barcodes_without_service_request = []
    # Check if there already exists a service request
    for barcode in barcodes:
        try:
            search_found = client.search_for_service_request(
                org="http://uri.d-t.se/id/Identifier/i-referral-code", org_referral_code=barcode)
            service_request_id = search_found["resource"]["id"]
            service_request_ids.append(service_request_id)
        except OrganizationReferralCodeNotFound as e:
            barcodes_without_service_request.append(barcode)

    click.echo("Found service requests for for {}/{} of the barcodes.".format(
        len(service_request_ids, len(barcodes))))

    # Create service requests if not exists
    for barcode in barcodes_without_service_request:
        try:
            service_request_id = create_anonymous_service_request(
                client, barcode)
            service_request_ids.append(service_request_id)
        except CouldNotCreateServiceRequest as e:
            click.echo(
                "FAILED IN CREATING SERVICE REQUEST. Could not create anonymous service request for barcode: {}".format(
                    barcode))
            raise e

    click.echo(
        "Created anonymous service requests for all non-registered samples...")

    # Send a failed result.
    try:
        for service_request_id in service_request_ids:
            send_results_to_partner(client, service_request_id)
    except PartnerClientAPIException as e:
        click.echo("FAILED IN POST RESULTS. Exception was:")
        raise e

    # TODO What should we do if a result has already been reported on this
    #      sample. Right now we will just fail, and I can't really think of
    #      a better way to do it.

    click.echo("Successfully sent failed results for all barcodes in file.")


def read_barcodes_from_file(filename):
    barcodes = []
    with open(filename) as f:
        for line in f:
            if "Referensnummer" in line:
                continue
            barcodes.append(line.split("\t")[0])

    click.echo("Read {} barcodes from file".format(len(barcodes)))
    return barcodes


if __name__ == '__main__':
    cli(obj={})
