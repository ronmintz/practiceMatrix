"""
Get Repo Quality: User quality is the fraction of user's pull requests which were
successfully merged or zero if user made no pull requests.
"""

import json
import sqlite3
from datetime import datetime
from datetime import timedelta
from common import format
from common import merge_period
from uuid import uuid4


def get_fraction_merged_for_users_and_repos(con):

    user_data = {}
    repo_data = {}

    fraction_merged_for_users = {} # fraction merged dictionary for each user who made a pull request
    fraction_merged_for_repos = {} # fraction merged dictionary for each repo with a pull request
    cur = con.cursor()

    sql = """
        select "user.login_h", "base.repo.full_name_h", merged, created_at, merged_at
        from pr_state
        where state = "closed"
        """
    cur.execute(sql)

    while True:
        row = cur.fetchone()
        if row == None:
            break

        try:
            user, repo, merged, created_at, merged_at = row

            if not(user in user_data):
                user_data[user] = [0,0]
#               user_data[user] [0] is merged count for this user
#               user_data[user] [1] is non-merged count for this user

            if not(repo in repo_data):
                repo_data[repo] = [0,0]
#               repo_data[repo] [0] is merged count for this repo
#               repo_data[repo] [1] is non-merged count for this repo

            if merged:
                dt_created_at = datetime.strptime(created_at, format)
                dt_merged_at  = datetime.strptime(merged_at,  format)
                time_to_merge = dt_merged_at - dt_created_at

                if time_to_merge <= timedelta(days=merge_period):
                    merged_promptly = True
                else:
                    merged_promptly = False
            else:
                time_to_merge = None
                merged_promptly = False

            if merged_promptly:
                user_data[user][0] += 1  # inc merged count
                repo_data[repo][0] += 1  # inc merged count
            else:
                user_data[user][1] += 1  # inc non-merged count
                repo_data[repo][1] += 1  # inc non-merged count

        except:
            continue  # go on to next row if bad data (e.g. bad date format)

    for user in user_data.keys():
        try:
            fraction_merged_for_users[user] = float(user_data[user][0]) / (user_data[user][0] + user_data[user][1])
#           print(user, fraction_merged_for_users[user])
        except:
            continue

    for repo in repo_data.keys():
        try:
            fraction_merged_for_repos[repo] = float(repo_data[repo][0]) / (repo_data[repo][0] + repo_data[repo][1])
#           print(repo, fraction_merged_for_repos[repo])
        except:
            continue

    return (fraction_merged_for_users, fraction_merged_for_repos)



def get_fraction_of_issues_commented_for_users(con):

    user_data = {}
    fraction_commented_for_users = {}  # fraction commented dictionary for each user who created an issue
    cur = con.cursor()

    sql = """
        select "user.login_h", state, comments
        from issue_state
        """
    cur.execute(sql)

    while True:
        row = cur.fetchone()
        if row == None:
            break

        try:
            user, state, num_comments = row
        
            if not(user in user_data):
                user_data[user] = [0,0]
#               user_data[user] [0] is count of twice commented issues for this user
#               user_data[user] [1] is count of other issues for this user

            if int(num_comments) >= 2:
                user_data[user][0] += 1
            else:
                user_data[user][1] += 1
        except:
            continue

    for user in user_data.keys():
        try:
            fraction_commented_for_users[user] = float(user_data[user][0]) / (user_data[user][0] + user_data[user][1])
            print('\nget_fraction_of_issues_commented_for_users:')
            print(user, fraction_commented_for_users[user])
        except:
            continue

    return fraction_commented_for_users


# fraction_merged_for_users = dict of fraction of all pull requests merged
# for each user referenced by pr_state, which defines the user qualities.

def get_repo_quality(con, repo_id, fraction_merged_for_users):

    cur = con.cursor()

    user_quality = {}

    sql = """
        select "user.login_h"
        from pr_state
        where "base.repo.full_name_h" = ?
        """
    cur.execute(sql, (repo_id,)) # get all users who made a PR on this repo

    while True:
        row = cur.fetchone()

        if row == None:
            break

        user = row[0]

        if not(user in user_quality):
            if user in fraction_merged_for_users:
                user_quality[user] = fraction_merged_for_users[user]
            else:  # user has no closed pull requests
                user_quality[user] = 0.0


    sum_quality = 0.0
    n = 0

    print('\nget_repo_quality3:  user\tquality')

    for user, quality in user_quality.items():
        print(user, quality)
        sum_quality += quality
        n += 1

    if n > 0:
        repo_quality = sum_quality / n
    else:
        repo_quality = 0.0

    print("repo_quality = ", repo_quality)
    return repo_quality

