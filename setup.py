#
#  Copyright (C) 2012, Philippe LUC (pluc at pluc.fr)
#
#  Homepage: http://www.pluc.fr/
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup
setup(name='cron_calendar',
      version='0.1',
      scripts=[
          "bin/cron_calendar"],
      description='Query google calendar to program program execution',
      author="Philippe LUC",
      author_email="pluc@pluc.fr",
      packages=["cron_calendar_lib"],
      install_requires=[
          'google-api-python-client',
          'oauth2client',
          'httplib2',
          "gconf",
      ],

      classifiers=[
        # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Environment :: Console",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Utilities",
        ]
    )
