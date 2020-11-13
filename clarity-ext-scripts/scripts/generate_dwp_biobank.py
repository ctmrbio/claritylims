#!/usr/bin/env python
"""Generate deep well plate biobank substitute CSVs"""
__author__ = "Fredrik Boulund"

from sys import argv, exit
from datetime import datetime
import time
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("NUM_CSV",
        type=int,
        default=100,
        help="Number of files to generate [%(default)s]")

    if len(argv) < 2:
        parser.print_help()
        exit()

    return parser.parse_args()


def generate_plate():
    rows = "ABCDEFGH"
    cols = [n+1 for n in range(12)]

    date = datetime.now()

    plate_id = f"DWP{date.strftime('%y%m%d%S%f')}"[:-1]

    plate = {
        "plate_id": plate_id,
        "wells": []
    }
    for row in rows:
        for col in cols:
            well_id = f"{plate_id}{row}{col}"
            well = {
                "pos": f"{row}{col}", 
                "well_id": well_id,
            }
            plate["wells"].append(well)
    return plate


def write_csv(plate, filename):
    with open(filename, 'w') as outf:
        for well in plate["wells"]:
            outf.write(f"{well['pos']},{well['well_id']},{plate['plate_id']}\n")
            

if __name__ == "__main__":
    args = parse_args()

    for n in range(args.NUM_CSV):
        time.sleep(1e-2)  # Wait to ensure unique IDs
        plate = generate_plate()
        filename = f"{plate['plate_id']}.csv"
        write_csv(plate, filename)
        print(f"Wrote {filename}")