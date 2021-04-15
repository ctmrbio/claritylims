import logging
from clarity_ext.extensions import GeneralExtension

logger = logging.getLogger(__name__)

alphabet = "abcdefghijklmnopqrstuvwxyz"

class Extension(GeneralExtension):
    """
    Validate and rename pool(s)
    """
    def execute(self):
        start = self.context.start
        date = start.strftime("%Y%m%d")

        for idx, pool in enumerate(set(self._all_outputs)):
            used_adapters = [s.udf_adapter_id_forward for s in pool.samples]
            if len(used_adapters) != len(set(used_adapters)):
                self.usage_error("Cannot combine pools with overlapping adapters!")

            pool_member_plates = set([
                "{}-{}".format(s.udf_biobank_plate_id, s.udf_dual_barcode_primer_mix_id)
                for s in pool.samples
            ])
            pool.name = "{}_{}_{}".format(date, "_".join(pool_member_plates), alphabet[idx])
            self.context.update(pool)

            out_container = pool.container
            out_container.name = pool.name
            self.context.update(out_container)

    @property
    def _all_outputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
           yield "24-46735"
