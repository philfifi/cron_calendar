
  Copyright (C) 2012, Philippe LUC (pluc at pluc.fr)

  Homepage: http://www.pluc.fr/

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

===================================
           cron calendar
===================================

Sort of cron using google calendar for tasks.


This script connects to google calendar, check the start time of each
event, and executes any command given in the "description" field. It
uses the ``at`` daemon to execute the command. Make sure it is running
on your system.


Installation
------------

 - Check the default configuration file [cron_calendar.conf], and
   provide your own google developper keys.

 - Create a new google calendar, and fill the calendar ID into the
   configuration file.

 - launch the ``cron_calendar`` script, and authenticate as
   indicated. (you only have to do this step once)
