# -*- coding: utf-8 -*-


import os
from datetime import datetime, timedelta
import time
import subprocess
import shelve

import httplib2

# package python2-google-api-python-client
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
import gflags



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


def get_RFC3339(dt):
    "Returns a string of the correct format given a datetime object"
    if time.daylight != 0:
        tz_offset = time.altzone
    else:
        tz_offset = time.timezone
    tz_str = (tz_offset >= 0) and "-" or "+"
    tz_offset = abs(tz_offset) / 60
    tz_str += "%02d:%02d" % (tz_offset / 60, tz_offset % 60)

    return dt.strftime("%Y-%m-%dT%H:%M:%S") + tz_str

def from_RFC3339(s):
    "Returns a datetime object from the given string"
    dt = datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    return dt


class CronCalendar:
    """
    Should be called periodicaly, query the google calendar, and
    program AT daemon to execute commands from the 'description' field

    """

    def __init__(self,
                 conf,
                 verbose_level=0,
                 dryrun=False):
        self.conf = conf
        self.verbose_level = verbose_level
        self.dryrun = dryrun

    def get_calendar_service(self):
        " Connect to google calendar"
        storage = Storage(os.path.expanduser(self.conf.get("storage", "credential_file")))
        credentials = storage.get()


        FLAGS = gflags.FLAGS
        FLAGS.auth_local_webserver = False
        flow = OAuth2WebServerFlow(
            client_id=self.conf.get("google_api", "client_id"),
            client_secret=self.conf.get("google_api", "client_secret"),
            scope='https://www.googleapis.com/auth/calendar',
            user_agent='CronCalendar/1.0')

        if credentials is None or credentials.invalid == True:
            credentials = run(flow, storage)

        # Create an httplib2.Http object to handle our HTTP requests and authorize it
        # with our good Credentials.
        http = httplib2.Http()
        http = credentials.authorize(http)

        service = build("calendar", "v3", http=http)

        return service

    def __get_query_dt(self):
        self.shelve_dict = shelve.open(os.path.expanduser(self.conf.get("storage", "shelve_file")))

        dt_now = datetime.now()
        dt_now -= timedelta(seconds=dt_now.second, # Make it aligned to minutes starts
                            microseconds=dt_now.microsecond)

        # Make sure we don't query twice the same time range.
        if "last_time_max" in self.shelve_dict:
            dt_time_min = max(dt_now,
                              self.shelve_dict["last_time_max"])
        else:
            dt_time_min = dt_now

        dt_time_max = dt_now + timedelta(minutes=self.conf.getint("general", "advance_minute"))

        return dt_time_min, dt_time_max

    def __program_at(self,
                     res,
                     dt_time_min,
                     dt_time_max):
        " From the raw results from the google api, program AT"
        at = AtApi()

        if "items" in res:
            for event in res["items"]:
                start_str = event["start"]["dateTime"]
                dt = from_RFC3339(start_str)
                if not (dt_time_min <= dt < dt_time_max):
                    if self.verbose_level >= 1:
                        print "Start time not inside boundaries"
                    continue

                description_str = event.get("description")
                summary_str = event.get("summary")
                if not description_str:
                    if self.verbose_level >= 1:
                        print "No command for [%s] at %s" % (summary_str, dt)
                    continue

                for line in description_str.split("\n"):
                    cmd = line.strip()
                    if not cmd:
                        continue
                    if self.verbose_level >= 1:
                        print "Programming from [%s] at %s command: [%s]" % (summary_str, dt, cmd)
                    if not self.dryrun:
                        at.run_at(dt, cmd)


    def run(self):

        # Connect to google API
        self.service = self.get_calendar_service()

        dt_time_min, dt_time_max = self.__get_query_dt()

        if dt_time_min == dt_time_max:
            print "Nothing to query"
        else:

            time_min = get_RFC3339(dt_time_min)
            time_max = get_RFC3339(dt_time_max)

            if self.verbose_level >= 1:
                print "Querying calendar from", time_min, "to", time_max
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
                              dt_time_min,
                              dt_time_max)

            # If we are here, programmation went well, and we can update the range
            self.shelve_dict["last_time_min"] = dt_time_min
            self.shelve_dict["last_time_max"] = dt_time_max


