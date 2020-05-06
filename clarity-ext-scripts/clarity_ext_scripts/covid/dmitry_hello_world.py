from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    """
    This extension just writes 'hello world' to the UI
    """
    def execute(self):
        print("Hello world")
        print(self.context.current_step.udf_assign_to_workflow)

    def integration_tests(self):
        yield "24-44476"
