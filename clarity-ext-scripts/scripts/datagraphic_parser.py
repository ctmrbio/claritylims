#!/usr/bin/env python
# encoding: utf-8

"""
Parse daily exports of covid-19 results from Clarity LIMS and upload to SciLifeLab DataGraphics endpoint.
"""
__author__ = "Senthilkumar Panneersalvam, Fredrik Boulund"
__date__ = "2020-05"
__version__ = "1.3"

import argparse
import datetime
import logging
import requests
import os
import yaml
import csv
from collections import defaultdict

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
        self.date_stats = defaultdict(lambda: defaultdict(int))
        self.result_types = set()
        self.input_file = self._get_input_file()
    
    def parse_latest_data(self, set_to_negative, frozen_files):
        """Parse the input file and return a csv string of compiled data"""
        logging.info("Found LIMS data file '{}', parsing...".format(self.input_file))
        self.sdate = datetime.datetime.now()
        self.edate = datetime.datetime.now() - datetime.timedelta(days=1)
        with open(self.input_file, 'r') as ifl:
            reader = csv.DictReader(ifl, delimiter=",")
            for row in reader:
                name = row["Name"]
                date = row["KNM result uploaded date"]
                control = row["Control"]
                result = row["rtPCR covid-19 result latest"]

                # Move on to next sample without further processing if following conditions met
                if ('biobank' in name.lower() 
                    or 'discard' in name.lower()
                    or result == 'failed_entire_plate_by_failed_external_control' 
                    or date == '' 
                    or result == '' 
                    or control == 'Yes'):
                    continue

                # Replace failed outcome with more descriptive text
                if 'failed' in result:
                    result = "invalid/inconclusive"

                # Collect all types of result as separate set
                self.result_types.add(result)

                # Date of sample processed
                parsed_date = datetime.datetime.strptime(date.split('T')[0], '%y%m%d')
                formated_date = datetime.datetime.strftime(parsed_date, "%Y-%m-%d")

                # Ignore any data later than yesterday
                if parsed_date > self.edate:
                    continue

                # Get the unique name to check for duplicates
                uname = name.split('_')[0]

                # Check if result needs to be modified
                if uname in set_to_negative:
                    result = "negative"
                    logging.debug("%s found in set_to_negative" % uname)

                # If the sample already processed keep the most recent result
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
                if not self.sdate or parsed_date < self.sdate:
                    self.sdate = parsed_date
                self.date_stats[formated_date][result] += 1
                self.added_samples[uname] = "{}_{}".format(formated_date, result)
        logging.info("Finished parsing LIMS file")

        for frozen_file in frozen_files:
            self.append_frozen_data(frozen_file)

        logging.debug("Formatting parsed data")
        self.parsed_data = ["date,count,class"]
        for date in self._date_range(self.sdate, self.edate):
            for result in self.result_types:
                self.parsed_data.append(",".join([date, str(self.date_stats.get(date, {}).get(result, 0)), result]))
        self.parsed_data = "\n".join(self.parsed_data)
        logging.info("Finished formatting data for submission.")

    def put_parsed_data(self):
        """Send the parsed data to DataGraphic server"""
        logging.info("Initiating to PUT parsed data")
        response = requests.put(self.data_url, headers={'x-apikey': self.api_key}, data=self.parsed_data)
        response.raise_for_status()
        logging.info("Parsed data have been successfully PUT")

    def append_frozen_data(self, frozen_file):
        """Append frozen data to total results"""
        with open(frozen_file) as f:
            logging.debug("Opened frozen file for parsing...")
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
	        self.date_stats[row["date"]][row["class"]] += int(row["count"])
                self.result_types.add(row["class"])
                parsed_date = datetime.datetime.strptime(row["date"], '%Y-%m-%d')
                if parsed_date < self.sdate:
                    self.sdate = parsed_date
                logging.debug("Parsed %s from frozen file", row)
        logging.info("Finished parsing and appending frozen file stats.")
        
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
    parser.add_argument("--set-to-negative",  dest="set_to_negative",
            default="", help="File with identifiers whose result should be set to 'negative'.")
    parser.add_argument("--append-frozen-stats", dest="append_frozen_stats", nargs="+",
            default="", help="Append preformatted frozen statistics to final submitted results.")
    args = vars(parser.parse_args())
    config = yaml.safe_load(args['config'])
    
    # if input file given, would not try and find file
    if args['input_file']:
        config['input_file'] = args['input_file']
    
    # Create sets of unique identifiers whose results should be changed
    set_to_negative = set()
    if args["set_to_negative"]:
        try:
            set_to_negative = set(barcode.strip() for barcode in open(args["set_to_negative"]).readlines())
        except IOError:
            pass

    frozen_files = None
    if args["append_frozen_stats"]:
        frozen_files = args["append_frozen_stats"]

    dp = data_parser(config)
    dp.parse_latest_data(set_to_negative, frozen_files)
    if not args['no_put']:
        dp.put_parsed_data()
    if args['print']:
        dp.print_parsed_data()
