import logging
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as psql_insert
from sqlalchemy.inspection import inspect
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
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        status = self._upsert(self.Status,
            [{
                "sequencer_id": sequencer_id,
                "flowcell_id": flowcell_id,
                "samplesheet_uploaded": now,
            }],
        )

        samples = self._upsert(self.Sample, samplesheet)


    def _upsert(self, table, records):
        primary_keys = [key.name for key in inspect(table).primary_key]

        insert_statement = psql_insert(table).values(records)
        logger.info(insert_statement.compile())

        update_dict = {
            c.name: c
            for c in insert_statement.excluded
        }
        logger.info(update_dict)

        upsert_statement = insert_statement.on_conflict_do_update(
            index_elements=primary_keys,
            set_=update_dict,
        )
        logger.info(upsert_statement.compile())

        with self.db.connect() as conn:
            return conn.execute(upsert_statement)

        
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

        





