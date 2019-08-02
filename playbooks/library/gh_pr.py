#!/usr/bin/python

from ansible.module_utils.basic import *
from copy import copy

import re
import requests
import yaml


DOCUMENTATION = '''
---
module: gh_pr
short_description: Collects data about GitHub repo's PR and allows to list prs in repo
'''

EXAMPLES = '''
- name: read PR data from github repo
  gh_pr:
    command: read
    number: 2222
    repo: ""
    token: "..."
    organization: "ManageIQ"
  register: result

  gh_pr:
    command list
    repo: ""
    token: "..."
    organization: "ManageIQ"
    filter:
      state: open
  register all_prs
'''

base_url = "https://api.github.com/repos/{}/{}/pulls"
certain_pr_url = base_url + "/{}"
file_pr_url = certain_pr_url + '/files?page={}'


def get_pr(data):
    headers = {'Authorization': 'token {}'.format(data.get('token'))}
    url = certain_pr_url.format(data['organization'], data['repo'], data['number'])
    request_params = dict(headers=headers if data.get('token') else {},
                          verify=data['verify_ssl'])

    response = requests.get(url, **request_params).json()
    metadata = copy(response)
    metadata['commit'] = response['head']['sha']

    body = response.get('body', "")
    cmd = re.findall("{{(.*?)}}", body) or {}
    metadata['cmd'] = yaml.safe_load(cmd[0].replace('py.test', 'pytest')) if cmd else {}

    modified_files = []
    update_requirements = False

    page = 1
    while True:
        response = requests.get(file_pr_url.format(data['organization'],
                                                   data['repo'],
                                                   data['number'],
                                                   page),
                                **request_params)
        try:
            if not response.json():
                break
            for filen in response.json():
                filename = filen['filename']
                if filen['status'] != "deleted" and filen['status'] != "removed":
                    if filename.startswith('cfme/tests') or filename.startswith('utils/tests'):
                        modified_files.append(filename)
                if 'requirements/frozen.' in filename:
                    update_requirements = True
        except:
            break
        page += 1

    metadata['update_requirements'] = update_requirements
    metadata['modified_files'] = modified_files

    return metadata


def get_prs(data):
    headers = {'Authorization': 'token {}'.format(data.get('token'))}
    url = base_url.format(data['organization'], data['repo'])
    pr_state = data.get('filter', {}).pop('state', None) or 'all'  # can be all, open, closed
    request_params = dict(headers=headers if data.get('token') else {},
                          verify=data['verify_ssl'],
                          params={'per_page': 100, 'state': pr_state})

    all_prs = []

    def parse_response(response):
        prs = []
        for pr in response:
            if data.get('filter'):
                for item, value in data['filter'].items():
                    if pr.get(item) != value:
                        break
                else:
                    prs.append(pr)
            else:
                prs.append(pr)
        return prs

    first_response = requests.get(url, **request_params)
    all_prs.extend(parse_response(first_response.json()))

    if not first_response.links.get('next', {}).get('url'):
        return all_prs

    next_url = first_response.links['next']['url']

    while next_url:
        next_response = requests.get(next_url, **request_params)
        all_prs.extend(parse_response(next_response.json()))
        next_url = next_response.links.get('next', {}).get('url')
        print("url {}, collected prs {}".format(next_url, len(all_prs)))

    return all_prs


def main():
    fields = {
        "verify_ssl": {"default": True, "type": "bool"},
        "organization": {"required": True, "type": "str"},
        "repo": {"required": True, "type": "str"},
        "command": {"required": True, "type": "str"},

        # required in some cases to read details
        "token": {"required": False, "type": "str"},

        # valid with 'read' command only
        "number": {"default": None, "type": "int"},

        # valid with 'list' command only
        "filter": {"required:": False, "type": "dict"},
    }

    commands = {'list', 'read'}

    module = AnsibleModule(argument_spec=fields)
    if module.params['command'] == 'list':
        module.exit_json(meta=get_prs(module.params))
    elif module.params['command'] == 'read':
        module.exit_json(meta=get_pr(module.params))
    else:
        raise ValueError("Wrong command {} passed. "
                         "supported commands {}".format(module.params['command'],
                                                        ", ".join(commands)))


if __name__ == '__main__':
    main()
