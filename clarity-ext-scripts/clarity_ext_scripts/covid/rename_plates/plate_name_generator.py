from clarity_ext.domain.validation import UsageError


class InheritancePlateNameGenerator:
    """
    A plate name generator that 'inherits' the running number from the input container
    and handles versioning of plates
    """
    def running_number(self, output_container, context):
        """
        Assuming that there is a 1 to 1 match in the plate layout between source and
        target plate, fetch running number from the matching input plate
        """
        first_artifact = output_container.occupied[0].artifact
        for input, output in context.artifact_service.all_aliquot_pairs():
            if output.name == first_artifact.name and output.container.name == output_container.name:
                return self._get_running_number_for(input.container.name)
        raise UsageError('No input plate could be matched against this plate: {}'.format(output_container.name))

    def _get_running_number_for(self, container_name):
        split_name = container_name.split('_')
        if len(split_name) == 1:
            raise UsageError("The input plate doesn't follow the assumed naming standard: {} "
                             .format(container_name))
        return split_name[1]

    def add_version_number(self, base_name, context):
        next_version = self._get_next_free_version_number(base_name, context)
        return '{}.v{}'.format(base_name, next_version)

    def _get_next_free_version_number(self, name_base, context):
        max_number_versions = 10
        for i in range(1, max_number_versions):
            trial_name = '{}.v{}'.format(name_base, i)
            response = context.session.api.get_containers(name=trial_name)
            if len(response) == 0:
                return i
        raise UsageError('Max number of versions exceeded ({}). Please contact system adminstrator.'
                          .format(max_number_versions))
