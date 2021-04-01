import logging
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

from clarity_ext.cli import load_config

logger = logging.getLogger(__name__)

config = load_config()

Base = declarative_base()

class DNBSEQ_DB():
    """Connect to DNBSEQ Postgresql DB

    Requires configuration in ~/.config/clarity-ext/clarity-ext.config:
        dnbseq_db_url: postgresql://username:password@c1-ctmr-db.ki.se:5431
    """


    def __init__(self):
        db_url = config["dnbseq_db_url"]
        self.db = sa.create_engine(url=db_url)
        self.session = Session(self.db)

    def submit_samplesheet(self, sequencer_id, flowcell_id, samplesheet):
        """Submit samplesheet to postgresql DB
        """
        today = datetime.today().strftime('%Y-%m-%d')

        samplesheet_upload_date = self.Status(
            sequencer_id=sequencer_id, 
            flowcell_id=flowcell_id, 
            samplesheet_uploaded=today,
        )
        self.session.add(samplesheet_upload_date)

        samples = [
            self.Sample(
                sample_id=row["sample_id"],
                project_id=row["project_id"],
                flowcell_id=row["flowcell_id"],
                row_id=row["row_id"],
                lims_id=row["lims_id"],
                PCR_well=row["well"],
                adapter_id=row["adapter_id"],
                adapter_id_reverse=row["adapter_id_reverse"],
                sequencer_id=row["sequencer_id"],
                lane_id=row["lane_id"], 
                pool_id=row["pool_id"],
            )
            for row in samplesheet
        ]
        self.session.add_all(samples)

        self.session.flush()
        self.session.commit()
        
    def _get_sequencer_id(self, sequencer_name):
        sequencer = self.session\
            .query(self.Sequencer)\
            .filter_by(alias=sequencer_name).first()
        if sequencer:
            return sequencer.sequencer_id
        else:
            return None

    class Sequencer(Base):
        __tablename__ = "DNBSEQ_instrument"
        sequencer_id = sa.Column(sa.String, primary_key=True)
        sequencer_type = sa.Column(sa.String)
        alias = sa.Column(sa.String)

    class Status(Base):
        __tablename__ = "DNBSEQ_status"
        sequencer_id = sa.Column(sa.String, primary_key=True)
        flowcell_id = sa.Column(sa.String, primary_key=True)
        samplesheet_uploaded = sa.Column(sa.DateTime)

    class Sample(Base):
        __tablename__ = "DNBSEQ_sample"
        sample_id = sa.Column(sa.String, primary_key=True)
        project_id = sa.Column(sa.String, primary_key=True)
        flowcell_id = sa.Column(sa.String, primary_key=True)
        row_id = sa.Column(sa.Integer)
        lims_id = sa.Column(sa.String)
        PCR_well = sa.Column(sa.String)
        fragmentation = sa.Column(sa.String)
        adapter_set = sa.Column(sa.String)
        adapter_id = sa.Column(sa.String)
        adapter_id_reverse = sa.Column(sa.String)
        sequencer_id = sa.Column(sa.String)
        lane_id = sa.Column(sa.String)
        pool_id = sa.Column(sa.String)

        




