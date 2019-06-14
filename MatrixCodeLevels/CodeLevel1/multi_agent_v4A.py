"""
Matrix: Multi agent process.
"""

import json
import socket
import sqlite3
from pathlib import Path
from random import randint
from datetime import datetime
from datetime import timedelta
from math import log
from uuid import uuid4
from past_behavior_v4A import past_behavior_metric
from get_repo_quality3A import get_fraction_merged_for_users_and_repos
from get_repo_quality3A import get_repo_quality

import logbook

from _c_code import ffi, lib  # Ron's new line

_log = logbook.Logger(__name__)

#event types in order:
et = ["CreateEvent", "DeleteEvent", "ForkEvent", "IssuesEvent", "PullRequestEvent", "PushEvent", "WatchEvent"]

class RPCException(Exception):
    pass


class RPCProxy:  # pylint: disable=too-few-public-methods
    """
    RPC Proxy class for calling controller functions.
    """

    def __init__(self, sock):
        self.sock = sock
        self.fobj = sock.makefile(mode="r", encoding="ascii")

    def __del__(self):
        self.fobj.close()

    def call(self, method, **params):
        """
        Call the remote function.
        """

        _log.info("Calling method: {}", method)

        msg = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": method,
            "params": params
        }
        msg = json.dumps(msg) + "\n"  # NOTE: The newline is important
        msg = msg.encode("ascii")
        self.sock.sendall(msg)

        ret = self.fobj.readline()
        ret = json.loads(ret)

        if "jsonrpc" not in ret or ret["jsonrpc"] != "2.0":
            raise RPCException("Invalid RPC Response", ret)
        if "error" in ret:
            raise RPCException("RPCException", ret)

        return ret["result"]


def main_multi_agent(address, event_db, agent_ids_file, agent_id_start_idx,
                     num_agents_per_proc, num_repos):

    starting_time = datetime.now()

    agent_ids_file = Path(agent_ids_file)
    if not agent_ids_file.exists():
        print(f"Error while loading agent ids. The file, '{agent_ids_file}' "
              f"doesn't exist!")
        return

    # Read agent login_h values from the given file starting at
    # the agent_id_start_idx and for num_agents_per_proc many agents
    agent_ids = []
    with open(agent_ids_file, 'r') as agent_ids_file:
        count = 0
        for idx, line in enumerate(agent_ids_file):
            if idx >= agent_id_start_idx and count < num_agents_per_proc:
                agent_ids.append(line.rstrip("\r\n"))
                count += 1

    logbook.StderrHandler().push_application()

    # Convert address to tuple format
    # Input format: 127.0.0.1:8090
    address = address.strip().split(":")
    address = (address[0], int(address[1]))

    address_str = ":".join(map(str, address))
    _log.notice('Connecting to controller at: {0}', address_str)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(address)
        proxy = RPCProxy(sock)

        _log.notice("Opening event database: {}", event_db)
        con = sqlite3.connect(event_db)

        lib.initCommonNeuralNet()  # Ron's new line


        while True:
            round_info = proxy.call("can_we_start_yet")
            _log.info("Round {}", round_info)

            # if round is -1 we end the simulation
            if round_info['cur_round'] == -1:
                print('\ncompletion time:', str(datetime.now() - starting_time))
                return

            tt = randint(round_info['start_time'], round_info['end_time'] - 1)
            dt = datetime.utcfromtimestamp(tt)
            dt_str = dt.isoformat() + 'Z'
            events = []
            (fraction_merged_for_users, fraction_merged_for_repos) = get_fraction_merged_for_users_and_repos(con)

            for agent_id in agent_ids:
                ret = do_something_per_agent(con, agent_id, num_repos,
                                             round_info['cur_round'], dt_str,
                                             fraction_merged_for_users,
                                             fraction_merged_for_repos)
                events.extend(ret)

            proxy.call("register_events", events=events)

def normalize_count(data, dmin, dmax):
    if data == 0:
        data = 1
    data = log(data)

    if dmin == 0:
        dmin = 1
    dmin = log(dmin) 

    if dmax == 0:
        dmax = 1
    dmax = log(dmax) 

    if data < dmin:
        data = dmin

    if data > dmax:
        data = dmax

    return (data - dmin) / (dmax - dmin)

def normalize_delta(data, dmin, dmax):
    data = log(data + 2.0)
    dmin = log(dmin + 2.0) 
    dmax = log(dmax + 2.0) 

    if data < dmin:
        data = dmin

    if data > dmax:
        data = dmax

    return (data - dmin) / (dmax - dmin)

def do_something_per_agent(con: sqlite3.Connection, agent_id, num_repos,
                           round_num, dt_str,
                           fraction_merged_for_users, fraction_merged_for_repos):


    cur = con.cursor()
    sql = """
          select public_repos, followers, following
          from user
          where login_h = ?
          """
    cur.execute(sql, (agent_id,))
    public_repos, followers, following = cur.fetchone()

    public_repos = str(normalize_count(public_repos, 0.0, 132125.0))
    followers = str(normalize_count(followers, 0.0, 134452.0))
    following = str(normalize_count(following, 0.0, 52722.0))

    afeatures = public_repos + " " + followers + " " + following


    row = None

    while row == None:
        # choose a row_id at random, look up its features in database
        row_id = randint(1, num_repos)

        sql = """
              select full_name_h, watchers_count, forks_count, "issue.open_count", "issue.total_count"
              from repository
              where rowid = ?
              """
        cur.execute(sql, (row_id,))

        row = cur.fetchone() # if this returns None, choose another row_id and repeat

    repo_id, watchers_count, forks_count, issue_open_count, issue_total_count = row	# full_name_h is the repo_id

    if issue_total_count == None:  # database contains some null values for issue_total_count
        issue_total_count = issue_open_count

    watchers_count = str(normalize_count(watchers_count, 0.0, 291574.0))
    forks_count = str(normalize_count(forks_count, 0.0, 107293.0))
    issue_open_count = str(normalize_count(issue_open_count, 0.0, 51903.0))
    issue_total_count = str(normalize_count(issue_total_count, 0.0, 51903.0))


    rfeatures = watchers_count + " " + forks_count + " " + issue_open_count + " " + issue_total_count

                            # past behavior metric for each type of event
    past_behavior = past_behavior_metric(dt_str, 14, agent_id, con)
    pb0 = str(normalize_delta(past_behavior[et[0]], -1.0, 32969.0))
    pb1 = str(normalize_delta(past_behavior[et[1]], -1.0, 1295.0))
    pb2 = str(normalize_delta(past_behavior[et[2]], -1.0, 1700.0))
    pb3 = str(normalize_delta(past_behavior[et[3]], -1.0, 4742.0))
    pb4 = str(normalize_delta(past_behavior[et[4]], -1.0, 3353.0))
    pb5 = str(normalize_delta(past_behavior[et[5]], -1.0, 12261.67))
    pb6 = str(normalize_delta(past_behavior[et[6]], -1.0, 1398.0))

    past_behavior_features = pb0 + " " + pb1 + " " + pb2 + " " + pb3 + " " + pb4 + " " + pb5 + " " + pb6


    if agent_id in fraction_merged_for_users:
        user_acceptance = str(round(fraction_merged_for_users[agent_id],2))
    else:
        user_acceptance = "0" # this user has not made any closed pull requests

    if repo_id in fraction_merged_for_repos:
        repo_acceptance = str(round(fraction_merged_for_repos[repo_id],2))
    else:
        repo_acceptance = "0" # this repo does not have any closed pull requests

    repo_qual = get_repo_quality(con, repo_id, fraction_merged_for_users)
    rq_feature = str(round(repo_qual,2))  # should 0 be used instead of None

    inputs = afeatures + " " + rfeatures + " " + past_behavior_features + " " + user_acceptance + " " + repo_acceptance + " " + rq_feature


    pOuts = lib.runCommonNeuralNet(inputs.encode())
    # Return the set of events that need to be done in this round.
    outs = ffi.string(pOuts).decode()
    outlist = outs.split(':')


    events = [{
        "id_h": f"{agent_id}_{round_num}",
        # Changing field names to match with the original JSON schema from GitHub
        "actor": {"login_h": agent_id},
        "repo": {"full_name_h": repo_id},
        "type": outlist[0],
        # This is a custom payload not in GitHub data, so you'll have to handle this separately
        # By default this will be ignored as the field "last output" is not something GitHubStore
        # recognizes
#       "payload": {"last output": outlist[1]},

        # Need to provide a created_at time in the following format
        "created_at": dt_str,  #  "YYYY:MM:DDThh:mm:ssZ"

        # Also, optionally, you need to provide a logical created_at time
        "_l_created_at": round_num
    }]


    return events
