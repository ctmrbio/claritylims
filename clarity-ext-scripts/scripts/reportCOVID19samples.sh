#!/bin/bash
# Dmitry Chekmenev, 2020
# Cron job which extract all samples with their UDFs of Covid-19 Clarity LIMS Project

set -euo pipefail

current_date=`date +%Y%m%d`
echo "$(date) Running Clarity sample data export for covid19 on ${current_date}"

psql --pset footer --no-align --field-separator=',' --username='clarity' --dbname='ClarityDB' --file='/opt/gls/clarity/users/glsai/deployment/claritylims/clarity-ext-scripts/scripts/reportCOVID19samples.sql' --output="/tmp/report_${current_date}"

echo "$(date) Export completed"
