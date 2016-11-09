
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

Synthax for commands
--------------------

The description field accept severals tokens to launch commands,
Those token can be defined in configuration file

**1. No token at all**

Without any token each no-empty line will be executed separately at the start of the google calendar event

*To note:*
  * Several commands can be added per event, those will be programmed as independant AT command at start time

**2. Comment token '#'**

This allow to comment your commands meaning::

    # This is a comment that will be ignored

**3. Start-Stop tokens**

Those tokens(configurable in config file) are followed by command that will be launched respectively to start of the event and to the end of the event::

    start: <cmd_launch_at_start>
    stop: <cmd_launch_at_end>

*To note:*
 * Commands 'start/stop' can be used several time per event, those will be
   programmed as independant AT command


**4. IF/ELSE token**

Those token allow inline in description field to condition execution of 2 commands
according to the result of third one(test_command)::

    if test_command return 0     then the test is PASSED and start/stop command can be launched (if defined)
    if test_command return other then the test is FAILED and else_start/else_stop command can be launched (if defined)

* For example description could look like::

    start: <start_commandA>
    if_start: <test_commandB>
    else_start: <start_commandC>

    stop: <stop_commandD>
    if_stop: <test_commandE>
    else_stop: <stop_commandF>

* This would be traduce as following pseudo code::

    -- at start time --
    IF test_commandB == 0:
      start_commandA
    ELSE:
      start_commandC

    -- at stop time --
    IF test_commandE == 0:
      start_commandD
    ELSE:
      start_commandF

*To note:*
 * IF/ELSE mechanisme is triggered if 'if_<start/stop>' is used
 * This use bash synthax '&&, ||', AT command should be launch as bash commands
 * If 'if_<start/stop>' token is used several time, only the first one will be used as test_comman



