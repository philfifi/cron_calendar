#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import os
from datetime import datetime, timedelta
import time
import subprocess
import shelve
import re

import httplib2

# package python2-google-api-python-client
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run_flow
from oauth2client import tools


class AtError(Exception):
    pass

class AtApi:
    def __init__(self,
                 verbose_level=0):
        self.verbose_level = verbose_level

    def run_at(self, dt, cmd):
        "Program the AT daemon to run the cmd at the given datetime"
        dt_now = datetime.now()
        delta_minutes = max(0,
                            (dt - dt_now).total_seconds() / 60 +1)
        at_cmd_l = ["at", "now + %d minutes" % delta_minutes]

        p = subprocess.Popen(at_cmd_l,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT
            )
        p.stdin.write(cmd + "\n")
        p.stdin.close()
        ret = p.wait()
        if ret != 0:
            raise AtError(p.stdout.readlines())


def get_RFC3339(dt_utc):
    "Returns a string of the correct format given a datetime object"
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

def from_RFC3339(s):
    "Returns a datetime object from the given string"
    dt = datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    return dt

def utc_from_RFC3339(s):
    "Returns a datetime object from the given string"
    dt = datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    assert s[22] == ":"
    utcoffset = timedelta(hours=int(s[20:22]), minutes=int(s[23:25]))
    sig = s[19]
    assert sig in "+-"
    if sig == "+":
        return dt - utcoffset
    else:
        return dt + utcoffset

class CronCalendar:
    """
    Should be called periodicaly, query the google calendar, and
    program AT daemon to execute commands from the 'description' field

    """
    tokenMatchRegExp=r"""^ \s* {} (?P<cmd_match>.+)"""

    def __init__(self,
                 conf,
                 logger,
                 verbose_level=0,
                 dryrun=False):
        self.conf = conf
        self.logger = logger
        self.verbose_level = verbose_level
        self.dryrun = dryrun

    def get_calendar_service(self):
        " Connect to google calendar"
        storage = Storage(os.path.expanduser(self.conf.get("storage", "credential_file")))
        credentials = storage.get()


        flow = OAuth2WebServerFlow(
            client_id=self.conf.get("google_api", "client_id"),
            client_secret=self.conf.get("google_api", "client_secret"),
            scope='https://www.googleapis.com/auth/calendar',
            user_agent='CronCalendar/1.0')

        if credentials is None or credentials.invalid == True:
            flags = tools.argparser.parse_args(args=["--noauth_local_webserver"])
            credentials = run_flow(flow, storage, flags)

        # Create an httplib2.Http object to handle our HTTP requests and authorize it
        # with our good Credentials.
        http = httplib2.Http()
        http = credentials.authorize(http)

        service = build("calendar", "v3", http=http)

        return service

    def __get_query_utc_dt(self):
        self.shelve_dict = shelve.open(os.path.expanduser(self.conf.get("storage", "shelve_file")))

        dt_utcnow = datetime.utcnow()
        dt_utcnow -= timedelta(seconds=dt_utcnow.second, # Make it aligned to minutes starts
                               microseconds=dt_utcnow.microsecond)

        # Make sure we don't query twice the same time range.
        if "last_utctime_max" in self.shelve_dict:
            dt_utctime_min = max(dt_utcnow,
                              self.shelve_dict["last_utctime_max"])
        else:
            dt_utctime_min = dt_utcnow

        dt_utctime_max = dt_utcnow + timedelta(minutes=self.conf.getint("general", "advance_minute"))

        return dt_utctime_min, dt_utctime_max

    def __match_stop(self, at, event, dt_utctime_min, dt_utctime_max):
        " Try to match Stop token in the decription field of event, if match programm At with command, return True, else False "
        cmdToken = self.conf.get("general", "stop_token")
        logger.debug("--match_stop with token: {}".format(cmdToken))
        re_cmd = re.compile(self.tokenMatchRegExp.format(cmdToken), re.VERBOSE|re.IGNORECASE)
        return self.__match_cmd(at, event, dt_utctime_min, dt_utctime_max, "end", re_cmd)

    def __match_start(self, at, event, dt_utctime_min, dt_utctime_max):
        " Try to match Start token in the decription field of event, if match programm At with command, return True, else False "
        cmdToken = self.conf.get("general", "start_token")
        logger.debug("--match_start with token: {}".format(cmdToken))
        re_cmd = re.compile(self.tokenMatchRegExp.format(cmdToken), re.VERBOSE|re.IGNORECASE)
        return self.__match_cmd(at, event, dt_utctime_min, dt_utctime_max, "start", re_cmd)

    def __match_none(self, at, event, dt_utctime_min, dt_utctime_max):
        logger.debug("--match_none")
        "Run whatever is in the description field of event, if match programm At with command, return True, else False "
        re_cmd = re.compile(self.tokenMatchRegExp.format(""), re.VERBOSE|re.IGNORECASE)
        return self.__match_cmd(at, event, dt_utctime_min, dt_utctime_max, "start", re_cmd)

    def __match_cmd(self,
                    at,
                    event,
                    dt_utctime_min,
                    dt_utctime_max,
                    cmd, reg_comp):
        # Start Event is in the range
        cmd_str = event[cmd]["dateTime"]
        cmd_dt = from_RFC3339(cmd_str)
        cmd_dt_utc = utc_from_RFC3339(cmd_str)
        if (cmd == "start") and not(dt_utctime_min <= cmd_dt_utc < dt_utctime_max):
            logger.debug("{} time not inside boundaries(min<=dt<max)".format(cmd))
        elif (cmd == "end") and not (dt_utctime_min < cmd_dt_utc <= dt_utctime_max):
            logger.debug("{} time not inside boundaries(min<dt<=max)".format(cmd))
        else:
            description_str = event.get("description")
            summary_str = event.get("summary")
            if not description_str:
                logger.debug("No command for [{}] at {}".format(summary_str, str(cmd_dt)))
            else:
                for line in description_str.split("\n"):
                    match = reg_comp.match(line)
                    if match:
                        if self.verbose_level >= 1:
                            print "Line: '{}' match".format(line)
                        if not match.group('cmd_match'):
                            continue
                        if self.verbose_level >= 1:
                            print "{}: Programming from [{}] at {} command: [{}]".format(cmd,summary_str, cmd_dt, match.group('cmd_match'))
                        if not self.dryrun:
                            at.run_at(cmd_dt, match.group('cmd_match'))
                        return True
                    else:
                        logger.debug("Line: '{}' doesn't match".format(line))
        return False

    def __program_at(self,
                     res,
                     dt_utctime_min,
                     dt_utctime_max):
        " From the raw results from the google api, program AT"
        at = AtApi()

        if "items" in res:
            for event in res["items"]:
                token_found  = self.__match_start(at, event, dt_utctime_min, dt_utctime_max)
                token_found |= self.__match_stop(at, event, dt_utctime_min, dt_utctime_max)
                if not token_found:
                    self.__match_none(at, event, dt_utctime_min, dt_utctime_max)

    def run(self):

        # Connect to google API
        self.service = self.get_calendar_service()

        dt_utctime_min, dt_utctime_max = self.__get_query_utc_dt()

        if dt_utctime_min == dt_utctime_max:
            logger.info("Nothing to query")
        else:

            time_min = get_RFC3339(dt_utctime_min)
            time_max = get_RFC3339(dt_utctime_max)

            logger.debug("Querying calendar from", time_min, "to", time_max)
            req = self.service.events().list(calendarId=self.conf.get("general", "calendar_id"),
                                             singleEvents=True,  # Make sure regular events are expanded
                                             orderBy="startTime",
                                             timeMin=time_min,
                                             timeMax=time_max
                                             )

            res = req.execute()

            if self.verbose_level >= 2:
                from pprint import pprint
                pprint(res)

            self.__program_at(res,
                              dt_utctime_min,
                              dt_utctime_max)

            # If we are here, programmation went well, and we can update the range
            self.shelve_dict["last_utctime_min"] = dt_utctime_min
            self.shelve_dict["last_utctime_max"] = dt_utctime_max
