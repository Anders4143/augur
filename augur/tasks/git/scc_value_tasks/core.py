from datetime import datetime
import logging
import requests
import json
import os
import subprocess
import re
import traceback
from augur.application.db.models import *
from augur.application.db.session import DatabaseSession
from augur.application.config import AugurConfig
from augur.tasks.github.util.github_api_key_handler import GithubApiKeyHandler
from augur.application.db.util import execute_session_query
from augur.tasks.util.worker_util import parse_json_from_subprocess_call

def value_model(session,repo_git,repo_id, path):
    """Runs scc on repo and stores data in database
        :param repo_id: Repository ID
        :param path: absolute file path of the Repostiory
    """

    session.logger.info('Generating value data for repo')
    session.logger.info(f"Repo ID: {repo_id}, Path: {path}")
    session.logger.info('Running scc...')

    path_to_scc = os.environ['HOME'] + '/scc'

    required_output = parse_json_from_subprocess_call(session.logger,['./scc', '-f','json','--by-file', path], cwd=path_to_scc)
    
    session.logger.info('adding scc data to database... ')
    session.logger.debug(f"output: {required_output}")

    to_insert = []
    for record in required_output:
        for file in record['Files']:
            repo_labor = {
                'repo_id': repo_id,
                'rl_analysis_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'programming_language': file['Language'],
                'file_path': file['Location'],
                'file_name': file['Filename'],
                'total_lines': file['Lines'],
                'code_lines': file['Code'],
                'comment_lines': file['Comment'],
                'blank_lines': file['Blank'],
                'code_complexity': file['Complexity'],
                'repo_url': repo_git,
                'tool_source': 'value_model',
                'data_source': 'Git',
                'data_collection_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            to_insert.append(repo_labor)
    
    session.insert_data(to_insert, RepoLabor, ["repo_id", "rl_analysis_date", "file_path", "file_name" ])

    session.logger.info(f"Done generating scc data for repo {repo_id} from path {path}")
