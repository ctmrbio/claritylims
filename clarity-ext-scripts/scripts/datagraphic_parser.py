#!/usr/bin/env python
# encoding: utf-8

"""
Parse daily exports of covid-19 results from Clarity LIMS and upload to SciLifeLab DataGraphics endpoint.
"""
__author__ = "Senthilkumar Panneersalvam"
__date__ = "2020-05"
__version__ = "1.1"

import argparse
import datetime
import logging
import requests
import os
import yaml

# Set logging level and format
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class data_parser(object):
    """
        Parser class takes in config with neccesary info and parse
        lims data dump and PUT it to DataGraphic page
    """
    def __init__(self, config):
        self.config = config
        self.api_key = self.config['scilifelab_datagraphics_api_key']
        self.data_url = self.config['scilifelab_datagraphics_data_url']
        self.added_samples = {}
        self.date_stats = {}
        self.result_types = set()
        self.input_file = self._get_input_file()
    
    def parse_latest_data(self):
        """Parse the input file and return a csv string of compiled data"""
        logging.info("Found LIMS data file '{}', parsing...".format(self.input_file))
        with open(self.input_file, 'r') as ifl:
            header = ifl.readline().strip().split(',')
    
            # Get the index of interested columns
            name_index = header.index('Name')
            control_index = header.index('Control')
            date_index = header.index('KNM result uploaded date')
            result_index = header.index('rtPCR covid-19 result latest')
            sdate = None
            edate = datetime.datetime.now() - datetime.timedelta(days=1)
            
            for line in ifl:
                columns = [l.strip() for l in line.strip().split(',')]
                # Get column info based on the index
                name = columns[name_index]
                date = columns[date_index]
                control = columns[control_index]
                result = columns[result_index]
                # Move on to next sample without further processing if following conditions met
                if ('biobank' in name.lower() or 'discard' in name.lower() or
                    result == 'failed_entire_plate_by_failed_external_control' or
                    date == '' or result == '' or control == 'Yes'):
                    continue
                # better phrasing of failed samples
                if 'failed' in result:
                    result = "invalid/inconclusive"
                # Collect all types of result as separate set
                self.result_types.add(result)
                # Date of sample processed
                parsed_date = datetime.datetime.strptime(date.split('T')[0], '%y%m%d')
                formated_date = datetime.datetime.strftime(parsed_date, "%Y-%m-%d")
                # Get the unique name to check for duplicates
                uname = name.split('_')[0]
                # If the sample already processed keep the recent result
                if uname in self.added_samples:
                    udate, uresult = self.added_samples.split('_')
                    if datetime.datetime.strptime(udate, '‰Y-%m-%d') > parsed_date:
                        continue
                    self.date_stats[udate][uresult] -= 1
                # Since date is the key here keeping it primary key
                if formated_date not in self.date_stats:
                    self.date_stats[formated_date] = {}
                if result not in self.date_stats[formated_date]:
                    self.date_stats[formated_date][result] = 0
                # Find the start and end range of date to iterate over
                if not sdate or parsed_date < sdate:
                    sdate = parsed_date
                # This would mostly never happen, but to catch in case
                if parsed_date > edate:
                    edate = parsed_date
                self.date_stats[formated_date][result] += 1
                self.added_samples[uname] = "{}_{}".format(formated_date, result)

        self.parsed_data = ["date,count,class"]
        for date in self._date_range(sdate, edate):
            for result in self.result_types:
                self.parsed_data.append(",".join([date, str(self.date_stats.get(date, {}).get(result, 0)), result]))
        self.parsed_data = "\n".join(self.parsed_data)
        logging.info("Finished parsing LIMS file")

    def put_parsed_data(self):
        """Send the parsed data to DataGraphic server"""
        logging.info("Initiating to PUT parsed data")
        response = requests.put(self.data_url, headers={'x-apikey': self.api_key}, data=self.parsed_data)
        response.raise_for_status()
        logging.info("Parsed data have been successfully PUT")
    
    def print_parsed_data(self):
        """Print parsed data to stdout"""
        print(self.parsed_data)
    
    def _get_input_file(self):
        """Get input file either from argument or try locate"""
        return self.config.get('input_file') or os.path.join(self.config['scilifelab_datagraphics_input_dir'], 
                                                             "report_{}".format(datetime.datetime.strftime(datetime.date.today(), "%Y%m%d")))
    
    def _date_range(self, sdate, edate):
        """Generator to give range of date from start to end"""
        days = (edate-sdate).days
        while not days < 0:
            yield datetime.datetime.strftime((sdate + datetime.timedelta(days=days)), "%Y-%m-%d")
            days -= 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=". ".join([__doc__, __author__, __version__]))
    parser.add_argument("-c", "--config", required=True, type=argparse.FileType('r'),
                        help="Config file with required info")
    parser.add_argument("-i", "--input_file", default=None, type=str,
                        help="Pass input file (intended for testing)")
    parser.add_argument("--print", action="store_true", help="Print the data after parsing")
    parser.add_argument("--no_put", action="store_true", help="Don't put data to server")
    args = vars(parser.parse_args())
    config = yaml.safe_load(args['config'])
    
    # if input file given, would not try and find file
    if args['input_file']:
        config['input_file'] = args['input_file']

    dp = data_parser(config)
    dp.parse_latest_data()
    if not args['no_put']:
        dp.put_parsed_data()
    if args['print']:
        dp.print_parsed_data()
