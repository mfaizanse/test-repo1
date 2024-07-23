import os
import time
import requests
import json
import datetime

##############################################################################
# NOTE: This script is used in the GitHub Actions workflow.
# Make sure any changes are compatible with the existing workflows.
##############################################################################

# This script waits for git check to completed.
# There are two types of git statuses i.e. check runs and statuses.
# For more information, see # https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks#types-of-status-checks-on-github

# Required env variables:
# - GITHUB_TOKEN                   - GitHub token for authentication.
# - REPOSITORY_FULL_NAME           - Repository name including owner name e.g. kyma-project/kyma-companion.
# - GIT_REF                        - Git reference to check for the check run (i.e. commit sha, branch name or tag name).
# - GIT_CHECK_RUN_NAME             - Name of the git check to wait for.
# - INTERVAL                       - Interval in seconds to wait before check the status again.
# - TIMEOUT                        - Timeout in seconds to wait for the check run to complete before failing.

def read_inputs():
    githubToken = os.environ.get("GITHUB_TOKEN")
    repository_full_name = os.environ.get('REPOSITORY_FULL_NAME')
    git_ref = os.environ.get('GIT_REF')
    git_check_run_name = os.environ.get('GIT_CHECK_RUN_NAME')

    # read and convert to integer.
    timeout = os.environ.get('TIMEOUT') # seconds
    try:
        timeout = int(timeout)
    except Exception:
        exit('ERROR: Input timeout is not an integer')

    # read and convert to integer.
    interval = os.environ.get('INTERVAL') # seconds
    try:
        interval = int(interval)
    except Exception:
        exit('ERROR: Input interval is not an integer')

    return {
        "token": githubToken,
        "repository_full_name": repository_full_name,
        "git_ref": git_ref,
        "git_check_run_name": git_check_run_name,
        "timeout": timeout,
        "interval": interval,
    }

def print_inputs(inputs):
    print('**** Using the following configurations: ****')
    print('Repository Full Name: {}'.format(inputs['repository_full_name']))
    print('Git REF : {}'.format(inputs['git_ref']))
    print('Git Check Run Name : {}'.format(inputs['git_check_run_name']))
    print('Timeout : {}'.format(inputs['timeout']))
    print('Interval : {}'.format(inputs['interval']))

def fetch_check_runs(repo, git_ref, token):
    url = "https://api.github.com/repos/{}/commits/{}/check-runs".format(repo, git_ref)
    reqHeaders = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Authorization' : 'Bearer {}'.format(token)
    }

    print('Fetching check runs from {}'.format(url))
    response = requests.get(url, headers=reqHeaders)
    if response.status_code != 200:
        raise Exception('API call failed. Status code: {}, {}'.format(response.status_code, response.text))
    return response.json()

def get_latest_check_run(check_run_name, check_runs):
    result = None
    latest_start_time = None
    for run in check_runs:
        if run['name'] == check_run_name:
            start_time = run['started_at'] # e.g. "2024-07-23T14:04:47Z"
            parsed_dt = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
            if latest_start_time is None or parsed_dt > latest_start_time:
                latest_start_time = parsed_dt
                result = run
    return result

def main():
    inputs = read_inputs()
    print_inputs(inputs)

    startTime = time.time() # seconds
    while True:
        print('****************************************************************************************')
        if (time.time() - startTime) > inputs['timeout']:
            print('Error: Timed out!')
            exit(1)

        # fetch check runs from github.
        check_runs = fetch_check_runs(inputs['repository_full_name'], inputs['git_ref'], inputs['token'])

        # extract the latest check run (because there may be multiple runs by same name).
        latest_check_run = get_latest_check_run(inputs['git_check_run_name'], check_runs['check_runs'])

        # print details of the latest check run.
        print('Found Check run: {} ({})'.format(latest_check_run['name'], latest_check_run['html_url']))
        print('Check run Head-SHA: {}'.format(latest_check_run['head_sha']))
        print('Check run start-at: {}'.format(latest_check_run['started_at']))
        print('Check run status: {}'.format(latest_check_run['status']))
        print('Check run conclusion: {}'.format(latest_check_run['conclusion']))

        if latest_check_run['status'] != 'completed':
            print('Check run not completed. Waiting...')
            time.sleep(inputs['interval'])
            continue

        if latest_check_run['conclusion'] == 'success':
            print('Check run completed with success.')
            exit(0)

        # failure|neutral|cancelled|skipped|timed_out
        if latest_check_run['conclusion'] in ['failure', 'neutral', 'cancelled', 'skipped', 'timed_out']:
            print('Check run completed with failure.')
            exit(1)

        result = check_commit_status_for_success(inputs)
        if result["concluded"]:
            jsonStr = json.dumps(result["commitStatus"])
            setActionOutput('state', result["commitStatus"]['state'])
            setActionOutput('json', jsonStr)
            print(result["commitStatus"])
            exit(result["exitCode"])

        # Sleep for `interval`.
        time.sleep(inputs['interval'])


if __name__ == "__main__":
    main()