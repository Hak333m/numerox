import os
import time
import requests

API_TOURNAMENT_URL = 'https://api-tournament.numer.ai'


# ---------------------------------------------------------------------------
# high-level user functions

def download_dataset(saved_filename):
    "Download the current Numerai dataset"
    url = 'https://api.numer.ai/competitions/current/dataset'
    r = requests.get(url)
    if r.status_code != 200:
        msg = 'failed to download dataset (staus code {}))'
        raise IOError(msg.format(r.status_code))
    with open(saved_filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=1024):
            fd.write(chunk)


def upload_submission(full_filename, public_id, secret_key):
    """
    Upload tournament submission (csv file) to Numerai.

    This function assume that the scope of your token is both
    upload_submission and read_submission_info.
    """
    t0 = time.time()
    api = Numerai(public_id, secret_key)
    if not api.has_token():
        raise ValueError("Must supply public_id, secret_key")
    filename = os.path.basename(full_filename)
    auth_query = \
        '''
        query($filename: String!) {
            submission_upload_auth(filename: $filename) {
                filename
                url
            }
        }
        '''
    submission_resp = api.call(auth_query, {'filename': filename})
    submission_auth = submission_resp['data']['submission_upload_auth']
    file_object = open(full_filename, 'rb').read()
    requests.put(submission_auth['url'], data=file_object)
    create_query = \
        '''
        mutation($filename: String!) {
            create_submission(filename: $filename) {
                id
            }
        }
        '''
    create = api.call(create_query, {'filename': submission_auth['filename']})
    submission_id = create['data']['create_submission']['id']

    # diplay status until complete
    seen = []
    print("            minutes")
    fmt = "{:>10.6f}  {:<.4f}  {:<}"
    while True:
        status = submission_status(submission_id, public_id, secret_key)
        for key, value in status.items():
            if value is not None and key not in seen:
                seen.append(key)
                t = time.time()
                minutes = (t - t0) / 60
                print(fmt.format(value, minutes, key))
        if len(status) == len(seen):
            break
        time.sleep(1)

    return submission_id


def submission_status(submission_id, public_id, secret_key):
    "display submission status"
    api = Numerai(public_id, secret_key)
    if not api.has_token():
        raise ValueError("Must supply public_id, secret_key")
    query = \
        '''
        query submissions($submission_id: String!) {
          submissions(id: $submission_id) {
            originality {
              pending
              value
            }
            concordance {
              pending
              value
            }
            consistency
            validation_logloss
          }
        }
        '''
    variable = {'submission_id': submission_id}
    status_raw = api.call(query, variable)
    status_raw = status_raw['data']['submissions'][0]
    status = {}
    for key, value in status_raw.items():
        if value is None:
            value = None
        elif isinstance(value, dict):
            value = value['value']
        status[key] = value
    return status


# ---------------------------------------------------------------------------
# low-level numerai api functions

class Numerai(object):

    def __init__(self, public_id=None, secret_key=None):
        if public_id and secret_key:
            self.token = (public_id, secret_key)
        elif not public_id and not secret_key:
            self.token = None
        else:
            print("You supply both a public id and a secret key.")
            self.token = None

    def has_token(self):
        if self.token is not None:
            return True
        return False

    def call(self, query, variables=None):
        body = {'query': query,
                'variables': variables}
        headers = {'Content-type': 'application/json',
                   'Accept': 'application/json'}
        if self.token:
            public_id, secret_key = self.token
            headers['Authorization'] = \
                'Token {}${}'.format(public_id, secret_key)
        r = requests.post(API_TOURNAMENT_URL, json=body, headers=headers)
        return r.json()