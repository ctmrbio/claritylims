from clarity_ext.extensions import GeneralExtension


class Extension(GeneralExtension):
    """
    A helloworld extension!
    """
    def execute(self):
        print(self.config['covid.test_partner_url'],
              self.config['covid.test_partner_user'],
              self.config['covid.test_partner_password'])

    def integration_tests(self):
        yield "24-38707"
