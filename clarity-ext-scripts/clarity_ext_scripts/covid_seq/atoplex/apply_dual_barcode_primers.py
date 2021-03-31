import os
import pandas as pd
from clarity_ext.extensions import GeneralExtension

class Extension(GeneralExtension):
    """
    Apply dual barcode indexing primers to all samples in a plate.
    """

    VALID_PRIMER_MIXES = [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    ]

    def parse_primer_mix(self, dual_barcode_primer_id):
        if not dual_barcode_primer_id in VALID_PRIMER_MIXES:
            self.usage_error("Selected dual barcode primer ID not valid!")

        script_dir = os.path.dirname(__file__)
        rel_path_primer_mix_file = "primer_mixes/dual_barcode_primer_mix960_{}.csv".format(
                dual_barcode_primer_id,
        )
        primer_mix_file = os.path.join(script_dir, rel_path_primer_mix_file)

        return pd.read_csv(primer_mix_file, index_col="well", dtypes={"well": str, "barcode": int})

    def execute(self):
        selected_primer_mix = self.context.current_step.udf_dual_barcode_primer_id
        primer_mix = self.parse_primer_mix(selected_primer_mix)

        for artifact in self._all_outputs:
            artifact.udf_map.force("Adapter id forward", primer_mix[artifact.well])
            artifact.udf_map.force("Adapter id reverse", primer_mix[artifact.well])

    @property
    def _all_outputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
        yield "24-46735"
