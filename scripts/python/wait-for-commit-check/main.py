import os
import time
import requests
import datetime

##############################################################################
# NOTE: This script is used in the GitHub Actions workflow.
# Make sure any changes are compatible with the existing workflows.
##############################################################################

# This script waits for git check to be completed.
# There are two types of git statuses i.e. check runs and statuses.
# For more information, see # https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks#types-of-status-checks-on-github

# Required env variables:
# - GITHUB_TOKEN                   - GitHub token for authentication.
# - REPOSITORY_FULL_NAME           - Repository name including owner name e.g. kyma-project/kyma-companion.
# - GIT_REF                        - Git reference to check for the check run (i.e. sha, branch name or tag name).
# - GIT_CHECK_RUN_NAME             - Name of the git check to wait for.
# - INTERVAL                       - Interval in seconds to wait before check the status again.
# - TIMEOUT                        - Timeout in seconds to wait for the check run to complete before failing.


def read_inputs():
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token is None or github_token == '':
        exit('ERROR: Env GITHUB_TOKEN is missing')

    repository_full_name = os.environ.get('REPOSITORY_FULL_NAME')
    if repository_full_name is None or repository_full_name == '':
        exit('ERROR: Env REPOSITORY_FULL_NAME is missing')

    git_ref = os.environ.get('GIT_REF')
    if git_ref is None or git_ref == '':
        exit('ERROR: Env GIT_REF is missing')

    git_check_run_name = os.environ.get('GIT_CHECK_RUN_NAME')
    if git_check_run_name is None or git_check_run_name == '':
        exit('ERROR: Env GIT_CHECK_RUN_NAME is missing')

    # read and convert to integer.
    timeout = os.environ.get('TIMEOUT') # seconds
    try:
        timeout = int(timeout)
    except Exception:
        exit('ERROR: Env TIMEOUT is missing or not an integer')

    # read and convert to integer.
    interval = os.environ.get('INTERVAL') # seconds
    try:
        interval = int(interval)
    except Exception:
        exit('ERROR: Env INTERVAL is missing or not an integer')

    return {
        "token": github_token,
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
    # https://docs.github.com/en/rest/checks/runs?apiVersion=2022-11-28#list-check-runs-for-a-git-reference
    url = "https://api.github.com/repos/{}/commits/{}/check-runs".format(repo, git_ref)
    req_headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Authorization': 'Bearer {}'.format(token)
    }

    print('Fetching check runs from {}'.format(url))
    response = requests.get(url, headers=req_headers)
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

    start_time = time.time() # seconds
    while True:
        print('****************************************************************************************')
        # Sleep for `interval`.
        # sleeping before first check, so that any pending workflow on Git ref is triggered/updated.
        time.sleep(inputs['interval'])

        # check if timeout has reached.
        elapsed_time = time.time() - start_time
        print('Elapsed time: {} secs (timout: {} secs)'.format(elapsed_time, inputs['timeout']))
        if elapsed_time > inputs['timeout']:
            print('Error: Timed out!')
            exit(1)

        # fetch check runs from GitHub.
        check_runs = fetch_check_runs(inputs['repository_full_name'], inputs['git_ref'], inputs['token'])

        # extract the latest check run (because there may be multiple runs by same name).
        latest_check_run = get_latest_check_run(inputs['git_check_run_name'], check_runs['check_runs'])
        if latest_check_run is None:
            print('Check run not found. Waiting...')
            continue

        # print details of the latest check run.
        print('Found Check run: {} ({})'.format(latest_check_run['name'], latest_check_run['html_url']))
        print('Check run Head-SHA: {}'.format(latest_check_run['head_sha']))
        print('Check run start-at: {}'.format(latest_check_run['started_at']))
        print('Check run status: {}'.format(latest_check_run['status']))
        print('Check run conclusion: {}'.format(latest_check_run['conclusion']))

        if latest_check_run['status'] != 'completed':
            print('Check run not completed. Waiting...')
            continue

        if latest_check_run['conclusion'] == 'success':
            print('Check run completed with success.')
            exit(0)

        # https://docs.github.com/en/rest/checks/runs?apiVersion=2022-11-28#list-check-runs-for-a-git-reference
        if latest_check_run['conclusion'] in ['failure', 'neutral', 'cancelled', 'skipped', 'timed_out']:
            print('Check run completed with failure.')
            exit(1)


if __name__ == "__main__":
    main()
