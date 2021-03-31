import os
import logging
import pandas as pd
from clarity_ext.extensions import GeneralExtension

logger = logging.getLogger(__name__)

class Extension(GeneralExtension):
    """
    Transfer barcode primers to output samples
    """

    def execute(self):

        for in_aliquot, out_aliquot in self._all_aliquot_pairs:
            logger.info(in_aliquot.udf_adapter_id_forward)
            logger.info(in_aliquot.udf_adapter_id_reverse)
            logger.info(out_aliquot.udf_adapter_id_forward)

        for in_container, out_container in self.context.containers:
            logger.info(in_container.name)
            logger.info(out_container.name)

        # 1. Verify that all adapters in input samples are unique
        # 2. Name output container according to some scheme
        # 3. Transfer adapter_id info to output container/samples somehow

    @property
    def _all_outputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def _all_inputs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    @property
    def _all_aliquot_pairs(self):
        return [artifact for _, artifact in self.context.artifact_service.all_aliquot_pairs()]

    def integration_tests(self):
        yield "24-46735"
