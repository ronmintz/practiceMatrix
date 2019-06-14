"""
Recent Past Behaviors analysis.  Version 4 of past_behavior.
Count number of events of each type in a time period ending at current time
and in the preceding time period of equal length for a specific user.
Compute metric for change from the previous time period to last time period.
"""

import json
import time
import sqlite3
from datetime import datetime
from datetime import timedelta
from common import event_db
from common import format
from uuid import uuid4


# count_events returns dictionary of number of events of each type
# that occur between dt1 and dt2 for user_id.
def count_events(dt1, dt2, user_id, con):

    cur = con.cursor()

    event_count = { "CreateEvent": 0,
                    "DeleteEvent": 0,
                    "ForkEvent":   0,
                    "IssuesEvent": 0,
                    "PullRequestEvent": 0,
                    "PushEvent":   0,
                    "WatchEvent":  0 }

    dtstr1 = dt1.strftime(format)
    dtstr2 = dt2.strftime(format)

    print(dtstr1, dtstr2)

    timeA = datetime.now()

    if user_id == "":
        sql = """
            select type
            from event
            where (created_at >= ?)
            and   (created_at <  ?)
            """
        cur.execute(sql, (dtstr1, dtstr2))
    else:
        sql = """
            select type
            from event
            where "actor.login_h" = ?
            and (created_at >= ?)
            and (created_at <  ?)
            """
        cur.execute(sql, (user_id, dtstr1, dtstr2))

    while True:
        row = cur.fetchone()
        if row == None:
            break

        (etype,) = row


        if etype in event_count:
            event_count[etype] += 1

    timeB = datetime.now()
    print('\ntime in count_events query=', str(timeB-timeA))

    for etype in event_count.keys():
        print(etype, event_count[etype])

    return event_count


def past_behavior_metric(current_timestr, period_length, user_id, con):
    print ('running version 4 of past_behavior')
    dt_current_time = datetime.strptime(current_timestr, format)
    delta = timedelta(days=period_length)

    print("\nFor user ", user_id)
    print("\nevent count for last period:")
    last_period = count_events(dt_current_time-delta, dt_current_time, user_id, con)


    print("\nevent count for previous period:")
    prev_period = count_events(dt_current_time-2*delta, dt_current_time-delta, user_id, con)

    print("\ntype", "                   metric")

    result = {}

    for etype in last_period.keys():
        if prev_period[etype] > 0:
            result[etype] = round(float(last_period[etype]) / prev_period[etype] - 1, 2)
        else:
            result[etype] = 0

        print(etype, result[etype])

    return result
