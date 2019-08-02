#!/usr/bin/python

from ansible.module_utils.basic import *
from copy import copy

import json
import requests

DOCUMENTATION = '''
---
module: gh_commit
short_description: Allows to set/get GitHub Repo's commit data and status
'''

EXAMPLES = '''
- name: Set status of commit from github repo
  gh_commit:
    sha: <some sha>
    repo: ""
    token: "..."
    organization: "ManageIQ"
    command: set_status
    status: <some values>   # set if present; get if absent
  register: result

- name: Get data and status of commit from github repo
  gh_commit:
    sha: <some sha>
    repo: ""
    token: "..."
    organization: "ManageIQ"
    command: read
  register: result
'''

commit_url = "https://api.github.com/repos/{}/{}/commits/{}"
commit_status_url = commit_url + "/statuses"


def read_commit(data):
    headers = {'Authorization': 'token {}'.format(data.get('token'))}
    curl = commit_url.format(data['organization'], data['repo'], data['sha'])
    request_params = dict(headers=headers if data.get('token') else {},
                          verify=data['verify_ssl'])

    commit_data = copy(requests.get(curl, **request_params).json())

    # read commit statuses
    stat_url = commit_status_url.format(data['organization'], data['repo'], data['sha'])
    stats_data = copy(requests.get(stat_url, **request_params).json())
    commit_data['statuses'] = stats_data

    return commit_data


def set_commit_status(data):
    headers = {'Authorization': 'token {}'.format(data.get('token'))}
    stat_url = commit_status_url.format(data['organization'], data['repo'], data['sha'])
    request_params = dict(headers=headers if data.get('token') else {},
                          verify=data['verify_ssl'])

    response = requests.post(stat_url, data=json.dumps(data['status']), **request_params).json()
    return response


def main():
    fields = {
        "verify_ssl": {"default": True, "type": "bool"},
        "organization": {"required": True, "type": "str"},
        "repo": {"required": True, "type": "str"},
        "command": {"required": True, "type": "str"},  # read, set_status

        # required in some cases to read details
        "token": {"required": False, "type": "str"},

        "sha": {"required": True, "type": "str"},


        "status": {'default': None, "type": "dict"},
    }

    commands = {'read', 'update_status'}

    module = AnsibleModule(argument_spec=fields)

    if module.params['command'] == 'read':
        module.exit_json(meta=read_commit(module.params))
    elif module.params['command'] == 'set_status':
        module.exit_json(meta=set_commit_status(module.params))
    else:
        raise ValueError("Wrong command {} passed. "
                         "supported commands {}".format(module.params['command'],
                                                        ", ".join(commands)))


if __name__ == '__main__':
    main()
