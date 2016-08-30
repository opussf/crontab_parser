#! /usr/bin/env python
# iso-8859-1 -*
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02110-1301, USA.
#
# Crontab-like string parse. Inspired on crontab.py of the
# gnome-schedule-1.1.0 package.
#
# Edited by Robinson Farrar (RFDaemoniac) July 2011
#
# Rewritten by Charles Gordon (Opus_SF)
#

import re
import datetime

class SimpleCrontabEntry( object ):
	"""Contrab-like parser.

	Only deals with the first 5 fields of a normal crontab entry.
	"""

	def __init__(self, entry = None ):
		self.__setup()
		self.set_value( entry )

	def set_value( self, entry = None ):
		self.data = entry
		if not self.data:
			self.fields = None
			return
		self.data = entry.lower()
		if self.data in self.special.keys():  # look for special entries and replace them
			self.data = self.special[self.data]
		fields = re.findall("\S+", self.data) # split the fields
		if len(fields) != 5:
			raise ValueError( "Crontab entry needs 5 fields" )

		# store the seperate fields
		self.fields = {}
		self.fields["minute"] = fields[0]
		self.fields["hour"]   = fields[1]
		self.fields["day"]    = fields[2]
		self.fields["month"]  = fields[3]
		self.fields["weekday"]= fields[4]
		# convert the fields from strings to lists, report if an error.
		if not self.__is_valid():
			raise ValueError( "Bad cronstring" )

	def matches( self, checkTime = datetime.datetime.now() ):
		"""Checks if given time matches cron pattern.
		This takes a datetime object or epoch seconds"""
		if not self.fields:
			raise AttributeError("Crontab needs an entry to check against")
		if not isinstance( checkTime, (int, float, datetime.datetime) ):
			raise ValueError( "Time to check can only be an int, float, or a datetime object" )

		if isinstance( checkTime, (int, float) ):
			checkTime = datetime.datetime.fromtimestamp( checkTime )

		# if both the day and weekday are specific (not the * wildcard), they are additive in the match (or)
		if (self.weekdayIsSpecific and self.dayIsSpecific):
			return checkTime.month in self.fields['month'] and \
					checkTime.hour in self.fields['hour'] and \
					checkTime.minute in self.fields['minute'] and \
					(checkTime.day in self.fields['day'] or \
						checkTime.weekday() + 1 in [d or 7 for d in self.fields['weekday']])

		return checkTime.month in self.fields['month'] and \
				checkTime.day in self.fields['day'] and \
				checkTime.hour in self.fields['hour'] and \
				checkTime.minute in self.fields['minute'] and \
				checkTime.weekday() + 1 in [d or 7 for d in self.fields['weekday']]

	def next_run( self, startTime = datetime.datetime.now() ):
		"""Calculates when the next excution will be."""
		# start by adding a minute (don't want to return startTime)
		oneMinute = datetime.timedelta( minutes=1 )
		startTime += oneMinute
		while True:
			if self.matches( startTime ):
				return startTime
			else:
				startTime += oneMinute

	def prev_run( self, startTime = datetime.datetime.now() ):
		"""Calculates when the previous execution was."""
		# start by subtracting a minute (don't want to return startTime)
		oneMinute = datetime.timedelta( minutes=1 )
		startTime -= oneMinute
		while startTime > datetime.datetime(1970, 1, 1):
			if self.matches( startTime ):
				return startTime
			else:
				startTime -= oneMinute
		raise ValueError( "Time goes before epoch" )

	def __iter__(self, startTime=datetime.datetime.now(), endTime=None ):
		"""Returns an iterator that lists all the times that the cronstring matches between startTime and endTime.
		If a single value is given, it will result in from now till then.
		"""
		try:	# use this to control
			if self.testTime:
				pass
		except:
			if not endTime:
				endTime = startTime
				startTime = datetime.datetime.now()
			self.testTime = startTime
			self.endTime = endTime
		return self
	next_runs = __iter__
	def next(self):
		self.testTime = self.next_run( self.testTime )
		if self.testTime > self.endTime:
			del self.testTime
			raise StopIteration
		return self.testTime

	#####  End of public methods

	def __setup( self ):
		self.weekdayIsSpecific = True
		self.dayIsSpecific = True
		self.fieldnames = {
			"minute"  : "Minute",
			"hour"    : "Hour",
			"day"     : "Day of Month",
			"month"   : "Month",
			"weekday" : "Day of Week",
		}
		self.special = {
			"@reboot"  : '',  # is this valid for this class?
			"@hourly"  : '0 * * * *',
			"@daily"   : '0 0 * * *',
			"@midnight": '0 0 * * *',
			"@weekly"  : '0 0 * * 0',
			"@monthly" : '0 0 1 * *',
			"@yearly"  : '0 0 1 1 *',
			"@annually": '0 0 1 1 *',
		}
		self.timeranges = {
			"minute"   : range(0,60),
			"hour"     : range(0,24),
			"day"      : range(1,32),
			"month"    : range(1,13),
			"weekday"  : range(0,8),
		}
		self.monthnames = {
			"1"        : "jan",
			"2"        : "feb",
			"3"        : "mar",
			"4"        : "apr",
			"5"        : "may",
			"6"        : "jun",
			"7"        : "jul",
			"8"        : "aug",
			"9"        : "sep",
			"10"       : "oct",
			"11"       : "nov",
			"12"       : "dec"
		}
		self.downames = {
			"0"  : "sun",
			"1"  : "mon",
			"2"  : "tue",
			"3"  : "wed",
			"4"  : "thu",
			"5"  : "fri",
			"6"  : "sat",
			"7"  : "sun",
		}

	def __is_valid( self ):
		"""Two fold function. Validate the cron entry by expanding the data.
		Returns True or False"""
		try: # step through the fields, expand them, report the exception
			for fieldName, expression in self.fields.items():
				self.__expand_field( fieldName, expression )
		except ValueError,(specific,caused,explanation):
			print("PROBLEM TYPE: %s, FIELD: %s -> %s" % ( specific, caused, explanation ))
			return False
		return True

	def __expand_field( self, fieldName, expression ):
		""" Takes the fieldname, and the expression to expand.
		Returns a list of valid values.
		Throws ValueError if there is a problem.
		"""
		#print("__expand_field( %s, %s )" % (fieldName, expression))
		timerange = self.timeranges[ fieldName ]

		# Replace alias names
		if fieldName == "month": alias = self.monthnames.copy()
		elif fieldName == "weekday": alias = self.downames.copy()
		else: alias = None
		if alias:
			for key, value in alias.iteritems():
				expression = re.sub("(?<!\w|/)"+ value +"(?!\w)", key, expression)

		# if both the day and weekday are specific (not the * wildcard), they are additive in the match (or)
		if re.match("\*", expression):
			if fieldName == "weekday": self.weekdayIsSpecific = False
			elif fieldName == "day": self.dayIsSpecific = False
		# Replace the wildcard with a range expression
		expression = expression.replace("*", "%s-%s" % (min(timerange), max(timerange)))

		# create a list of the comma seperated expressions
		expressionlist = expression.split(",")
		stepPattern = re.compile("^(\d+-\d+)/(\d+)$")
		rangePattern = re.compile("^(\d+)-(\d+)$")

		expressionRange = []
		for expr in expressionlist:
			step = 1  # set to one as a default
			rangeList = None

			result = stepPattern.match(expr)
			if result:  # This is a pattern with a step value
				expr = result.groups()[0]
				# store the step value, this catches 0, is that valid?
				step = int(result.groups()[1])
				# step needs to be in the timerange.  0-59/60 would only match one anyway
				if (step == 0) or (step not in timerange):
					raise ValueError("stepwidth",
							self.fieldnames[fieldName],
							"Step value (%s) must be in the range of %s-%s, and not 0." % (step, min(timerange), max(timerange)))

			# process the non-step data
			result = rangePattern.match(expr)
			if result:  # this is a range
				if (int(result.groups()[0]) not in timerange) or \
						(int(result.groups()[1]) not in timerange):
					# the range had invalid min or max values
					raise ValueError("range",
							self.fieldnames[fieldName],
							"Must be in the range of %s-%s." % (min(timerange), max(timerange)))
				# do the work, make the range list
				rangeList = range( int(result.groups()[0]), int(result.groups()[1])+1, step )

			elif not expr.isdigit(): # not a range, not a digit, raise exception
				raise ValueError("fixed",
						self.fieldnames[fieldName],
						"%s is not a number." % ( expr, ) )

			elif int(expr) not in timerange: # not a range, is a digit, check value
				raise ValueError("fixed",
						self.fieldnames[fieldName],
						"Must be in the range of %s-%s." % (min(timerange), max(timerange)))

			if rangeList:
				expressionRange.extend(rangeList)
			else:
				expressionRange.append(int(expr))

		# convert to a set and back to a list to remove duplicates
		expressionRange = list(set(expressionRange))
		# sort this?

		#print("Equates to: %s" % (expressionRange,))
		# push the generated list back to the field
		self.fields[fieldName] = expressionRange



###############


if __name__ == "__main__" :
	import datetime
	import unittest
	class CrontabTests( unittest.TestCase ):
		def setUp( self ):
			self.e = SimpleCrontabEntry()
		def tearDown( self ):
			self.e = None
		def test_instanceInitWithEntry( self ):
			self.e = None
			self.e = SimpleCrontabEntry("* * * * *")
			self.assertEqual( self.e.data, "* * * * *", "Given pattern is not stored in object." )
		def test_instanceInitWithoutEntry( self ):
			self.e = None
			self.e = SimpleCrontabEntry()
			self.assertIsNone( self.e.data, "This should still be None." )
		def test_set_value_noneResetsObject_thowsException_matches( self ):
			self.e.set_value("* * * * *")
			self.e.set_value(None)
			self.assertRaises( AttributeError, self.e.matches )
		def test_set_value_noneResetsObject_thowsException_next_run( self ):
			self.e.set_value("* * * * *")
			self.e.set_value(None)
			self.assertRaises( AttributeError, self.e.next_run )
		def test_set_value_noneResetsObject_thowsException_prev_run( self ):
			self.e.set_value("* * * * *")
			self.e.set_value(None)
			self.assertRaises( AttributeError, self.e.prev_run )
		def test_set_value_noneResetsObject_thowsException_next_runs( self ):
			self.e.set_value("* * * * *")
			self.e.set_value(None)
			self.assertRaises( AttributeError, self.e.next_runs )




		def test_set_value_setsFields( self ):
			self.e.set_value("* * * * *")
			self.assertEqual( 5, len(self.e.fields), "There needs to be 5 fields." )
		def test_set_value_throwsException_one( self ):
			self.assertRaises( ValueError, self.e.set_value, "*" )
		def test_set_value_throwsException_two( self ):
			self.assertRaises( ValueError, self.e.set_value, "* *" )
		def test_set_value_throwsException_three( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * *" )
		def test_set_value_throwsException_four( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * * *" )
		def test_set_value_throwsException_six( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * * * * *" )
		def test_set_value_throwsException_badStep_emptyStep( self ):
			self.assertRaises( ValueError, self.e.set_value, "*/ * * * *")
		def test_set_value_throwsException_badStep_outOfRange( self ):
			self.assertRaises( ValueError, self.e.set_value, "*/60 * * * *")
		def test_set_value_throwsException_badStep_0Step( self ):
			self.assertRaises( ValueError, self.e.set_value, "*/0 */0 */0 */0 */0" )
		def test_set_value_throwsException_badMinValue( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * 0-1 * *")
		def test_set_value_throwsException_badMaxValue( self ):
			self.assertRaises( ValueError, self.e.set_value, "58-60 * * * *")
		def test_set_value_throwsException_wildcardRangeNotValid( self ):
			self.assertRaises( ValueError, self.e.set_value, "*-* * * * *" )
		def test_set_value_throwsException_wildcardStepNotValid( self ):
			self.assertRaises( ValueError, self.e.set_value, "*/* * * * *" )
		def test_set_value_oddPatterns_01( self ):
			self.e.set_value("1-5,5-10,1-10 * * * *")
		def test_set_value_oddPatterns_02( self ):
			self.e.set_value("*,* * * * *")
		def test_set_value_oddPatterns_03( self ):
			self.e.set_value("59,58,57 * * * *")
			self.assertEqual( [57,58,59], self.e.fields["minute"])
		def test_set_value_oddPatterns_04( self ):
			self.e.set_value("* * * jan-dec/2 *")
		def test_set_value_handles_3charMonths_true( self ):
			self.e.set_value( "* * * jan-mar *" )
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1 ) ), "1/1/1970 is in Jan" )
		def test_set_value_handles_3charMonths_false( self ):
			self.e.set_value( "* * * FEB *" )
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1 ) ), "1/1/1970 is not in Feb" )
		def test_set_value_handles_3charMonths_2inARow( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * * febFEB *" )
		def test_set_value_handles_3charMonths_badValue( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * * 1FEB *" )
		def test_set_value_handles_3charMonths_list( self ):
			self.e.set_value( "* * * jan,jun *")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1 ) ), "1/1/1970 is in Jan" )
		def test_set_value_handles_3charDOW_true( self ):
			self.e.set_value( "* * * * thu" )
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1 ) ), "1/1/1970 is Thursday" )
		def test_set_value_handles_3charDOW_false( self ):
			self.e.set_value( "* * * * sun" )
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1 ) ), "1/1/1970 is not Sunday" )
		def test_set_value_handles_3charDOW_2inARow( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * * * sunmon" )
		def test_set_value_handles_3charDOW_badValue( self ):
			self.assertRaises( ValueError, self.e.set_value, "* * * * 1sun" )
		def test_matches_givenAString( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertRaises( ValueError, self.e.matches, "1970-6-10 8:30" )

		######## Special tests
		def test_matches_specialEntries_reboot_true( self ):
			"""Not sure what this may mean for this usage"""
			pass
		def test_matches_specialEntries_reboot_false( self ):
			"""Not sure what this may mean for this usage"""
			pass
		def test_matches_specialEntries_yearly( self ):
			self.e.set_value('@yearly')
			self.assertEqual( '0 0 1 1 *', self.e.data )
		def test_matches_specialEntries_annually( self ):
			self.e.set_value('@annually')
			self.assertEqual( '0 0 1 1 *', self.e.data )
		def test_matches_specialEntries_monthly( self ):
			self.e.set_value('@monthly')
			self.assertEqual( '0 0 1 * *', self.e.data )
		def test_matches_specialEntries_weekly( self ):
			self.e.set_value('@weekly')
			self.assertEqual( '0 0 * * 0', self.e.data )
		def test_matches_specialEntries_daily( self ):
			self.e.set_value('@daily')
			self.assertEqual( '0 0 * * *', self.e.data )
		def test_matches_specialEntries_midnight( self ):
			self.e.set_value('@midnight')
			self.assertEqual( '0 0 * * *', self.e.data )
		def test_matches_specialEntries_hourly( self ):
			self.e.set_value('@hourly')
			self.assertEqual( '0 * * * *', self.e.data )


		####### Tests from the original
		def test_matches_specificDayTime_seconds( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertTrue( self.e.matches( 13879800 ), "This should match." )
		def test_matches_specificDayTime_seconds_int( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertTrue( self.e.matches( 13879800 ) )
		def test_matches_specificDayTime_datetime( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 6, 10, 8, 30 ) ), "This should match." )
		def test_matches_specificDayTime_seconds_false( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertFalse( self.e.matches( 13879700 ) )
		def test_matches_specificDayTime_datetime_false( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 6, 10, 8, 31 ) ), "This should match." )
		def test_matches_dow( self ):
			self.e.set_value('* * * * 0')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 4 ) ), "1/4/1970 is Sunday." )
		def test_matches_dow_False( self ):
			self.e.set_value('* * * * 0')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1 ) ), "1/1/1970 is Thursday." )
		def test_matches_dow_andHour_True( self ):
			self.e.set_value('* 5 * * 7')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 4, 5 ) ), "1/4/1970 is Sunday." )
		def test_matches_dow_andHour_True( self ):
			self.e.set_value('* 5 * * 7')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1, 5 ) ), "1/1/1970 is Thursday." )
		def test_matches_dow_andHour_True( self ):
			self.e.set_value('* 5 * * 7')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 4 ) ), "1/4/1970 is Sunday, at midnight." )
		def test_matches_limitedHourList_True( self ):
			self.e.set_value('0 11,16 * * *')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1, 16 ) ) )
		def test_matches_limitedHourList_False( self ):
			self.e.set_value('0 11,16 * * *')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1, 11, 30 ) ) )
		def test_matches_limitedHourRange_True( self ):
			self.e.set_value('0 9-18 * * *')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1, 10 ) ) )
		def test_matches_limitedHourRange_False( self ):
			self.e.set_value('0 9-18 * * *')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1, 14, 30 ) ) )
		def test_matches_allStar_matches_01( self ):
			self.e.set_value('* * * * *')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1 ) ) )
		def test_matches_allStar_matches_02( self ):
			self.e.set_value('* * * * *')
			self.assertTrue( self.e.matches( datetime.datetime.now() ) )
		def test_matches_limitedMinute_complicatedParse_True( self ):
			self.e.set_value('0-10/2 * * * *')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1 ) ) )
		def test_matches_limitedMinute_complicatedParse_False_30( self ):
			self.e.set_value('0-10/2 * * * *')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1, 0, 30 ) ), "minute out side of range" )
		def test_matches_limitedMinute_complicatedParse_False_05( self ):
			self.e.set_value('0-10/2 * * * *')
			self.assertFalse( self.e.matches( datetime.datetime( 1970, 1, 1, 0, 5 ) ), "minute out side of range" )

		### next_run tests
		def test_next_run_01( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 1, 1) ) )
		def test_next_run_02( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 4, 1) ) )
		def test_next_run_03( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 6, 1) ) )
		def test_next_run_04( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 6, 6) ) )
		def test_next_run_05( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 6, 10) ) )
		def test_next_run_06( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 6, 10, 4) ) )
		def test_next_run_07( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 6, 10, 8) ) )
		def test_next_run_08( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 6, 10, 8, 15) ) )
		def test_next_run_09( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertEqual( datetime.datetime( 1971, 6, 10, 8, 30 ), self.e.next_run( datetime.datetime(1970, 6, 10, 8, 30) ) )
		def test_next_run_10( self ):
			self.e.set_value('0 11,16 * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 11, 0 ), self.e.next_run( datetime.datetime( 1970, 1, 1 ) ) )
		def test_next_run_11( self ):
			self.e.set_value('0 11,16 * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 16, 0 ), self.e.next_run( datetime.datetime( 1970, 1, 1, 14, 30 ) ) )
		def test_next_run_12( self ):
			self.e.set_value('0 9-18 * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 2, 9, 0 ), self.e.next_run( datetime.datetime( 1970, 1, 1, 19 ) ) )
		def test_next_run_13( self ):
			self.e.set_value('0 9-18 * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 15, 0 ), self.e.next_run( datetime.datetime( 1970, 1, 1, 14, 30 ) ) )
		def test_next_run_14( self ):
			self.e.set_value('0 9-18 * * 1-5')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 12, 0 ), self.e.next_run( datetime.datetime( 1970, 1, 1, 11 ) ) )
		def test_next_run_15( self ):
			self.e.set_value('0 9-18 * * 1-5')
			self.assertEqual( datetime.datetime( 1970, 1, 5, 9, 0 ), self.e.next_run( datetime.datetime( 1970, 1, 3, 14, 30 ) ) )
		def test_next_run_16( self ):
			self.e.set_value('* * * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 0, 1 ), self.e.next_run( datetime.datetime( 1970, 1, 1 ) ) )
		def test_next_run_17( self ):
			self.e.set_value('* * * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 14, 31 ), self.e.next_run( datetime.datetime( 1970, 1, 1, 14, 30 ) ) )
		def test_next_run_18( self ):
			self.e.set_value('0-10/2 * * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 0, 2 ), self.e.next_run( datetime.datetime( 1970, 1, 1 ) ) )
		def test_next_run_19( self ):
			self.e.set_value('0-10/2 * * * *')
			self.assertEqual( datetime.datetime( 1970, 1, 1, 14, 6 ), self.e.next_run( datetime.datetime( 1970, 1, 1, 14, 5 ) ) )

		def test_next_run_special_01( self ):
			self.e.set_value('0 20 * * 3') # 8pm on Wednesday
			self.assertEqual( datetime.datetime( 2016, 8, 31, 20, 0 ), self.e.next_run( datetime.datetime( 2016, 8, 24, 20, 0 ) ) )
		def test_next_run_special_02( self ):
			self.e.set_value('0 20 * * 3') # 8pm on Wednesday
			self.assertEqual( datetime.datetime( 2016, 9, 7, 20, 0 ), self.e.next_run( datetime.datetime( 2016, 8, 31, 20, 00 ) ) )
		def test_next_run_special_03( self ):
			self.e.set_value('0 20 * * 3') # 8pm on Wednesday
			self.assertEqual( datetime.datetime( 2016, 12, 7, 20, 0 ), self.e.next_run( datetime.datetime( 2016, 11, 30, 20, 00 ) ) )

		def test_prev_run_01( self ):
			self.e.set_value("30 8 10 6 *")
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.prev_run( datetime.datetime( 1971, 1, 1) ) )
		def test_prev_run_02( self ):
			self.e.set_value("30 8 10 6 *")
			self.assertEqual( datetime.datetime( 1970, 6, 10, 8, 30 ), self.e.prev_run( datetime.datetime( 1971, 6, 10, 8, 30 ) ) )
		def test_prev_run_03( self ):
			self.e.set_value("* 5 * * *")
			self.assertEqual( datetime.datetime( 1970, 3, 31, 5, 59 ), self.e.prev_run( datetime.datetime( 1970, 4, 1 ) ) )
		def test_prev_run_04( self ):
			self.e.set_value("0 11,16 * * *")
			self.assertEqual( datetime.datetime( 1970, 12, 31, 16, 0 ), self.e.prev_run( datetime.datetime( 1971, 1, 1 ) ) )
		def test_prev_run_05( self ):
			self.e.set_value("0 11,16 * * *")
			self.assertEqual( datetime.datetime( 1970, 1, 1, 11, 0 ), self.e.prev_run( datetime.datetime( 1970, 1, 1, 13, 30 ) ) )
		def test_prev_run_06( self ):
			self.e.set_value("0 9-18 * * *")
			self.assertEqual( datetime.datetime( 1970, 1, 1, 18, 0 ), self.e.prev_run( datetime.datetime( 1970, 1, 1, 19 ) ) )
		def test_prev_run_07( self ):
			self.e.set_value("0 9-18 * * *")
			self.assertEqual( datetime.datetime( 1970, 1, 1, 14, 0 ), self.e.prev_run( datetime.datetime( 1970, 1, 1, 14, 30 ) ) )
		def test_prev_run_08( self ):
			self.e.set_value("* * * * *")
			self.assertEqual( datetime.datetime( 1970, 12, 31, 23, 59 ), self.e.prev_run( datetime.datetime( 1971, 1, 1 ) ) )
		def test_prev_run_09( self ):
			self.e.set_value("* * * * *")
			self.assertEqual( datetime.datetime( 1970, 1, 1, 14, 29 ), self.e.prev_run( datetime.datetime( 1970, 1, 1, 14, 30 ) ) )
		def test_prev_run_10( self ):
			self.e.set_value("0-10/2 * * * *")
			self.assertEqual( datetime.datetime( 1970, 12, 31, 23, 10 ), self.e.prev_run( datetime.datetime( 1971, 1, 1 ) ) )
		def test_prev_run_11( self ):
			self.e.set_value("0-10/2 * * * *")
			self.assertEqual( datetime.datetime( 1970, 1, 1, 14, 6 ), self.e.prev_run( datetime.datetime( 1970, 1, 1, 14, 8 ) ) )
		def test_prev_run_12( self ):
			self.e.set_value("* 5 * * *")
			self.assertEqual( datetime.datetime( 1970, 4, 30, 5, 59 ), self.e.prev_run( datetime.datetime( 1970, 5, 1 ) ) )
		def test_prev_run_13( self ):
			self.e.set_value("2,3,5,7 10 29 2 *")
			self.assertEqual( datetime.datetime( 1972, 2, 29, 10, 7 ), self.e.prev_run( datetime.datetime( 1973, 1, 1 ) ) )
		def test_noCron_throwsException_matches( self ):
			self.e = None
			self.e = SimpleCrontabEntry()
			self.assertRaises( AttributeError, self.e.matches )
		def test_noCron_throwsException_next_run( self ):
			self.e = None
			self.e = SimpleCrontabEntry()
			self.assertRaises( AttributeError, self.e.next_run )
		def test_noCron_throwsException_prev_run( self ):
			self.e = None
			self.e = SimpleCrontabEntry()
			self.assertRaises( AttributeError, self.e.prev_run )
		def test_generator_listcomprehension( self ):
			self.e.set_value("0 20 * * sun")
			datelist = [d for d in self.e.next_runs( datetime.datetime( 2016, 1, 1 ), datetime.datetime( 2017, 1, 1 ))]
			self.assertEqual( 52, len(datelist) )
		def test_generator_leapday_notLeapYear( self ):
			self.e.set_value("0 0 29 * *")
			datelist = [d for d in self.e.next_runs( datetime.datetime( 2015, 1, 1 ), datetime.datetime(2016, 1, 1 ))]
			self.assertEqual( 11, len(datelist) )
		def test_generator_leapday_leapYear( self ):
			self.e.set_value("0 0 29 * *")
			datelist = [d for d in self.e.next_runs( datetime.datetime( 2016, 1, 1 ), datetime.datetime(2017, 1, 1 ))]
			self.assertEqual( 12, len(datelist) )
		def test_generator_big( self ):
			self.e.set_value("* * * * *")
			datelist = [d for d in self.e.next_runs( datetime.datetime( 2016, 1, 1 ), datetime.datetime(2017, 1, 1 ))]
			self.assertEqual( 527040, len(datelist) )
		def test_domdow_areAdditive_matches_first( self ):
			self.e.set_value("0 0 1,15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1, 0, 0 )), "Should match the 1st of the month." )
		def test_domdow_areAdditive_matches_sat_01( self ):
			self.e.set_value("0 0 1,15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 3, 0, 0 )), "Should match a Saturday." )
		def test_domdow_areAdditive_matches_sat_02( self ):
			self.e.set_value("0 0 1,15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 10, 0, 0 )), "Should match a Saturday." )
		def test_domdow_areAdditive_matches_sat_03( self ):
			self.e.set_value("0 0 1,15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 15, 0, 0 )), "Should match the 15th of the month." )
		def test_domdow_areAdditive_matches_sat_04( self ):
			self.e.set_value("0 0 1,15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 17, 0, 0 )), "Should match a Saturday." )
		def test_domdow_areAdditive_matches_sat_05( self ):
			self.e.set_value("0 0 1,15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 24, 0, 0 )), "Should match a Saturday." )
		def test_domdow_areAdditive_matches_sat_06( self ):
			self.e.set_value("0 0 1,15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 31, 0, 0 )), "Should match a Saturday." )
		def test_domdow_areAdditive_matches_domStep_01( self ):
			self.e.set_value("0 0 */2 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 1 )), "Should match the first." )
		def test_domdow_areAdditive_matches_domStep_02( self ):
			self.e.set_value("0 0 */2 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 10 )), "Should match that saturday." )
		def test_domdow_areAdditive_matches_2step( self ):
			self.e.set_value("0 0 */7,*/15 * sat")
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 1, 10 )), "Should match that saturday." )





	unittest.main()
