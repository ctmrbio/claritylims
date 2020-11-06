#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
from datetime import date, timedelta

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import pandas as pd

import psycopg2

def load_pgpass():
    """ Load connection parameters from ~/.pgpass 
    
    Will only load the first line in the file, assuming:
    
    host:port:database:user:password
    """
    with open(Path("~/.pgpass").expanduser()) as pgpass:
        host, port, database, user, password = pgpass.readline().strip().split(":")
    return {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }

def connect_to_db():
    """Connect to Clarity PostgreSQL database.
    """
    params = load_pgpass()
    params.update(port=server.local_bind_port)
    conn = psycopg2.connect(**params)
    curs = conn.cursor()
    print("PostgreSQL database connected")
    return conn, curs


def send_email(to_address, from_address, subject, attachment=None, server_address="send.ki.se"):
    """Send email with an optional attachment.
    """
    
    msg = MIMEMultipart()
    msg['Subject'] = subject 
    msg['From'] = from_address
    msg['To'] = to_address

    if attachment:
        assert Path(attachment).exists()
        filename = Path(attachment).name
        attach = MIMEBase('application', "octet-stream")
        attach.set_payload(open(attachment, 'rb').read())
        encoders.encode_base64(attach)
        attach.add_header('Content-Disposition', 'attachment; filename="{}"'.format(filename))
        msg.attach(attach)

    server = smtplib.SMTP(server_address)
    server.sendmail(from_address, to_address, msg.as_string())


if __name__ == "__main__":

    conn, curs = connect_to_db()

    db_query = """
    select
        p.luid as "LimsId", s.name as "Name", 
            pf2.text5 as "CT latest date",
            round(pf6.numeric6::numeric, 10)::float8 as "FAM-CT latest",
            round(pf22.numeric8::numeric, 10)::float8 as "VIC-CT latest",
            pf24.text5 as "rtPCR covid-19 result latest"
        from sample s inner join process p using(processid)
            left join processudfstorage pf2 on s.processid = pf2.processid and pf2.rowindex = 0
            left join processudfstorage pf6 on s.processid = pf6.processid and pf6.rowindex = 0
            left join processudfstorage pf22 on s.processid = pf22.processid and pf22.rowindex = 0
            left join processudfstorage pf24 on s.processid = pf24.processid and pf24.rowindex = 1
        where projectid = 3		-- prod02
        --where s.projectid = 2 -- COVID_Test project on prod02
        --where s.projectid = 51 -- COVID_Test project on stage02
        --where s.projectid = 101 -- Covid19 project on stage02
        order by 1
    """

    clarity = pd.read_sql(db_query, conn)

    clarity["report_datetime"] = pd.to_datetime(clarity["CT latest date"], format="%Y%m%dT%H:%M:%S")

    today = pd.to_datetime(date.today())
    yesterday = pd.to_datetime(today - timedelta(days = 1))
    yesterday

    alltid_oppet = clarity["Name"].str.contains("Alltidppet")
    biobank = clarity["Name"].str.contains("BIOBANK")
    reported_yesterday = (clarity["report_datetime"] >= yesterday) & (clarity["report_datetime"] < today)
    samples_reported_yesterday = clarity[alltid_oppet & ~biobank & reported_yesterday]

    columns = [
        "report_datetime",
        "Name",
        "FAM-CT latest",
        "VIC-CT latest",
        "rtPCR covid-19 result latest",
    ]

    pt = samples_reported_yesterday[columns].groupby(["rtPCR covid-19 result latest"]).count()["FAM-CT latest"]

    kul_data = pd.DataFrame(
        [{
            "Rapporterande verksamhet": "NPC",
            "Analystyp": "PCR",
            "Typ": "PEP",
            "Datum för provsvar": str(yesterday.date()),
            "Antal negativa": pt["negative"],
            "Antal positiva": pt["positive"],
            "Totalt antal prover": pt.sum(),
        }],
    ).set_index(["Rapporterande verksamhet", "Analystyp", "Typ"])

    export_filename = "/tmp/NPC_statistics_for_KUL_{}.xlsx".format(str(yesterday.date()))
    kul_data.to_excel(export_filename)

    send_email(
        to_address="fredrik.boulund@ki.se", 
        from_address="noreply.npc@ki.se", 
        subject="Test email from script", 
        attachment=export_filename,
    )
