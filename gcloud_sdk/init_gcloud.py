
# Built-in Imports
import os
import tempfile
import json

# Third Party Imports
from ecosystem_tests import utils


class GCPMissingVariableException(Exception):
    pass


class GCPErrorCodeException(Exception):
    pass


GCP_ACTIVATE_SERVICE_ACCOUNT = \
    'gcloud auth activate-service-account --key-file {0}'

GCP_SET_PROJECT = \
    'gcloud config set project {0}'


def get_gcp_service_account_template():
    """
    This is a template for service account content file that must be used in
    in order to be able to use gcloud command line inside circelci env
    :return:
    """
    return {
      'type': 'service_account',
      'project_id': '',
      'private_key_id': '',
      'private_key': '',
      'client_email': '',
      'client_id': '',
      'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
      'token_uri': 'https://accounts.google.com/o/oauth2/token',
      'auth_provider_x509_cert_url': 'https://www.googleapis.com/'
                                     'oauth2/v1/certs',
      'client_x509_cert_url': '',
    }


GCP_ENV_VARIABLES = {
    'client_x509_cert_url': 'GCP_CERT_URL',
    'client_email': 'GCP_EMAIL',
    'client_id': 'GCP_CLIENT_ID',
    'project_id': 'GCP_PRIVATE_PROJECT_ID',
    'private_key_id': 'GCP_PRIVATE_KEY_ID',
    'private_key': 'GCP_PRIVATE_KEY',
}


def populate_gcp_service_account():
    """
    This method will be used to populate the service account file
    for GCP so that it can be used to activate the GCP account
    :return:
    """
    service_account_map = get_gcp_service_account_template()
    for key, value in GCP_ENV_VARIABLES.items():
        try:
            gcp_var_value = os.environ[value]
        except KeyError:
            raise GCPMissingVariableException(
                'Missing environment variable {0}'.format(value))

        if key == 'private_key':
            gcp_var_value = gcp_var_value.decode('string_escape')

        if not gcp_var_value:
            raise GCPMissingVariableException(
                'Missing environment variable {0}'.format(value))

        service_account_map[key] = gcp_var_value

    return service_account_map


def generate_service_account_file():
    """
    This method will generate the path file for the service account that
    need to be used when activate the service account
    :return:
    """
    service_account_map = populate_gcp_service_account()
    service_account_file, name = tempfile.mkstemp(suffix='.json')
    os.write(service_account_file, json.dumps(service_account_map))
    os.close(service_account_file)
    return name


if __name__ == '__main__':
    # Get the file path for service account
    file_path = generate_service_account_file()

    # Enable to use service account authorization
    activate_return_code = utils.execute_command(
        GCP_ACTIVATE_SERVICE_ACCOUNT.format(file_path))

    if activate_return_code:
        raise GCPErrorCodeException(
            'Failed to activate service account command')

    # Set Service Account Project
    set_project_return_code = utils.execute_command(
        GCP_SET_PROJECT.format(os.environ['GCP_PRIVATE_PROJECT_ID']))

    if set_project_return_code:
        raise GCPErrorCodeException(
            'Failed to set google cloud project')

