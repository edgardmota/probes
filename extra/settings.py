#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Return Code Constants

class constants:

	#Return Code Constants
	NO_ERRORS = 0
	COMMAND_USE_ERROR = 1
	PARSING_CONFIGURATION_ERROR = 2
	CANT_READ_CONFIGURATION = 3

	#Periodicity Check Constants
	HOUR_DAILY_CHECK = 0
	SECOND_MINUTELY_CHECK = 0
	MINUTE_HOURLY_CHECK = 0

	SUBSECTIONS = [
	{u'name':u'dumps', u'type':'growing-dir'},
	{u'name':u'master-binlogs-rsync', u'type':'changing-dir'},
	{u'name':u'mysql-replication', u'type':'mysql-replication'},
        ]
