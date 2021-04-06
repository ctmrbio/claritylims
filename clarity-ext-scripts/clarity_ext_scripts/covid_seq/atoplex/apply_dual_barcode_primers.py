import os
import logging
import pandas as pd
from clarity_ext.extensions import GeneralExtension

logger = logging.getLogger(__name__)

VALID_PRIMER_MIXES = [
    "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
]

class Extension(GeneralExtension):
    """
    Apply dual barcode indexing primers to all samples in a plate.
    """

    def parse_primer_mix(self, dual_barcode_primer_id):
        if not dual_barcode_primer_id in VALID_PRIMER_MIXES:
            self.usage_error("Selected dual barcode primer ID not valid!")

        script_dir = os.path.dirname(__file__)
        rel_path_primer_mix_file = "primer_mixes/dual_barcode_primer_mix960_{}.csv".format(
                dual_barcode_primer_id,
        )
        primer_mix_file = os.path.join(script_dir, rel_path_primer_mix_file)

        return pd.read_csv(
            primer_mix_file, 
            index_col="well", 
            dtype={"well": str, "barcode": int}
        )

    def execute(self):
        selected_primer_mix = self.context.current_step.udf_dual_barcode_primer_id
        primer_mix_df = self.parse_primer_mix(selected_primer_mix)
        primer_map = primer_mix_df.to_dict(orient="index")

        for artifact in self._all_outputs:
            well = str(artifact.well.position).replace(":", "")
            original_sample = artifact.sample()
            original_sample.udf_map.force("Adapter id forward", str(primer_map[well]["barcode"]))
            original_sample.udf_map.force("Adapter id reverse", str(primer_map[well]["barcode"]))
            self.context.update(original_sample)

    @property
    def _all_outputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
        yield "24-46735"
