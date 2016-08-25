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
		#print("matches( %s ).  type: %s" % (checkTime,type(checkTime)))
		if not self.fields:
			raise AttributeError("Crontab needs an entry to check against")
		if not isinstance( checkTime, (int, float, datetime.datetime) ):
			raise ValueError( "Time to check can only be an int, float, or a datetime object" )

		if isinstance( checkTime, (int, float) ):
			checkTime = datetime.datetime.fromtimestamp( checkTime )
			print(checkTime)

		return checkTime.month in self.fields['month'] and \
				checkTime.day in self.fields['day'] and \
				checkTime.hour in self.fields['hour'] and \
				checkTime.minute in self.fields['minute'] and \
				checkTime.weekday() + 1 in [d or 7 for d in self.fields['weekday']]


	def __setup( self ):
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

#     def __next_time(self, time_list, time_now):
#         """Little helper function to find next element on the list"""
#         tmp = [x for x in time_list if x >= time_now]
#         carry = False
#         if len(tmp) == 0:
#             carry = True
#             sol = time_list[0]
#         else:
#             sol = tmp[0]
#         return sol, carry

#     def __prev_time(self, time_list, item):
#         """Little helper function to find previous element on the list"""
#         pos = time_list.index(item)
#         elem = time_list[pos-1]
#         carry = elem >= time_list[pos]
#         return elem, carry

#     def __next_month(self, month, sol):
#         """Find next month of execution given the month arg. If month
#         is different than current calls all the other __next_*
#         functions to set up the time."""

#         #print("__next_month(%s, %s)" % (month, sol))
#         #print("self.fields[month] = %s" % (self.fields['month'],))

#         sol['month'], carry = self.__next_time(self.fields['month'], month)
#         if carry :
#             sol['year'] += 1
#         if sol['month'] != month :
#             self.__next_day(1,sol)
#             self.__next_hour(0,sol)
#             self.__next_minute(0,sol)
#             return False
#         return True

#     def __next_minute(self, minute, sol):
#         """Find next minute of execution given the minute arg."""
#         sol['minute'], carry = self.__next_time(self.fields['minute'], minute)
#         if carry:
#             self.__next_hour(sol['hour']+1, sol)
#         return True

#     def __next_hour(self, hour, sol):
#         """Find next hour of execution given the hour arg. If hour is
#         different than current calls the __next_hour function to set
#         up the minute """

#         sol['hour'], carry = self.__next_time(self.fields['hour'], hour)
#         if carry:
#             self.__next_day(sol['day']+1, sol)
#         if sol['hour'] != hour:
#             self.__next_minute(0,sol)
#             return False
#         return True

#     #el weekday se calcula a partir del dia, el mes y ao dentro de sol
#     def __next_day(self, day, sol):
#         """Find next day of execution given the day and the month/year
#         information held on the sol arg. If day is different than
#         current calls __next_hour and __next_minute functions to set
#         them to the correct values"""
#         #print("__next_day( %s, %s )" % (day, sol))

#         try:
#             now = datetime.date(sol['year'], sol['month'], day)
#         except:
#             try:
#                 now = datetime.date(sol['year'], sol['month']+1, 1)
#                 #print("Good 2nd try")
#             except:
#                 now = datetime.date(sol['year']+1, 1, 1)
#         # The way is handled on the system is monday = 0, but for crontab sunday =0
#         weekday = now.weekday()+1
#         # first calculate day
#         day_tmp, day_carry = self.__next_time(self.fields['day'], day)
#         #print("day_tmp: %s, day_carry: %s" % (day_tmp, day_carry))
#         day_diff = datetime.date(sol['year'], sol['month'], day_tmp) - now

#         # if we have all days but we don't have all weekdays we need to
#         # perform different
#         if len(self.fields['day']) == 31 and len(self.fields['weekday']) != 8:
#             weekday_tmp, weekday_carry = self.__next_time(self.fields['weekday'], weekday)
#             # Both 0 and 7 represent sunday
#             weekday_tmp -= 1
#             if weekday_tmp < 0 : weekday_tmp = 6
#             weekday_diff = datetime.timedelta(days=weekday_tmp - (weekday - 1))
#             if weekday_carry :
#                 weekday_diff += datetime.timedelta(weeks=1)
#             weekday_next_month = (now + weekday_diff).month != now.month
#             #print("Weekday_next_month: %s" % (weekday_next_month,))
#             # If next weekday is not on the next month
#             if not weekday_next_month :
#                 sol['day'] = (now + weekday_diff).day
#                 if sol['day'] != day :
#                     self.__next_hour(0,sol)
#                     self.__next_minute(0, sol)
#                     return False
#                 return True
#             else :
#                 flag = self.__next_month(sol['month']+1, sol)
#                 if flag :
#                     return self.__next_day(0, sol)
#                 return False

#         # if we don't have all the weekdays means that we need to use
#         # them to calculate next day
#         #print("weekday: %s" % (self.fields['weekday'],))
#         if len(self.fields['weekday']) != 8:
#             weekday_tmp, weekday_carry = self.__next_time(self.fields['weekday'], weekday)
#             # Both 0 and 7 represent sunday
#             weekday_tmp -= 1
#             if weekday_tmp < 0 : weekday_tmp = 6
#             weekday_diff = datetime.timedelta(days=weekday_tmp - (weekday - 1))
#             if weekday_carry :
#                 weekday_diff += datetime.timedelta(weeks=1)
#             weekday_next_month = (now + weekday_diff).month != now.month
#             # If next weekday is not on the next month
#             if not weekday_next_month :
#                 #  If the next day is on other month, the next weekday
#                 #  is closer to happen so is what we choose
#                 if day_carry:
#                     sol['day'] = (now + weekday_diff).day
#                     if sol['day'] != day :
#                         self.__next_hour(0,sol)
#                         self.__next_minute(0, sol)
#                         return False
#                     return True
#                 else :
#                     # Both day and weekday are good candidates, let's
#                     # find out who is going to happen
#                     # sooner
#                     diff = min(day_diff, weekday_diff)
#                     sol['day'] = (now+diff).day
#                     if sol['day'] != day :
#                         self.__next_hour(0,sol)
#                         self.__next_minute(0, sol)
#                         return False
#                     return True

#         sol['day'] = day_tmp
#         if day_carry :
#             self.__next_month(sol['month']+1, sol)
#         if sol['day'] != day :
#             self.__next_hour(0,sol)
#             self.__next_minute(0, sol)
#             return False
#         return True


#     def matches(self, time = datetime.datetime.now()):
#         """Checks if given time matches cron pattern."""
#         if not self.fields:
#              raise AttributeError("Crontab needs an entry to check against")
#         return time.month in self.fields['month'] and \
#             time.day in self.fields['day'] and \
#             time.hour in self.fields['hour'] and \
#             time.minute in self.fields['minute'] and \
#             time.weekday() + 1 in [d or 7 for d in self.fields['weekday']] # Sunday may be represented as ``0`` or ``7``.


#     def next_run(self, time = datetime.datetime.now()):
#         """Calculates when will the next execution be."""
#         #print("next_run(%s)" % (time,))
#         if self.matches(time):
#             time += datetime.timedelta(minutes = 1)
#         sol = {'minute': time.minute, 'hour': time.hour, 'day': time.day, 'month' : time.month, 'year' : time.year}
#         # next_month if calculated first as next_day depends on
#         # it. Also if next_month is different than time.month the
#         # function will set up the rest of the fields
#         try:
#             self.__next_month(time.month, sol) and \
#                                           self.__next_day(time.day, sol) and \
#                                           self.__next_hour(time.hour, sol) and \
#                                           self.__next_minute(time.minute, sol)
#             #print("returning: ")
#             return datetime.datetime(sol['year'], sol['month'], sol['day'], sol['hour'], sol['minute'])
#         except:
#             try:
#                 return self.next_run(datetime.datetime(time.year, time.month+1, 1, 0, 0))
#             except:
#                 return self.next_run(datetime.datetime(time.year+1, 1, 1, 0, 0))

#     def __prev_date(self, base, prev_day, carry_day):
#         if carry_day:
#             prev_month=base.month
#             prev_year=base.year
#             i = 0
#             for i in xrange(7):
#                 prev_month, carry_month = self.__prev_time(self.fields['month'], prev_month)
#                 if carry_month:
#                     prev_year -= 1
#                 try:
#                     date = datetime.datetime(prev_year, prev_month, prev_day, base.hour, base.minute)
#                 except ValueError:
#                     pass
#                 else:
#                     if date.weekday() in self.fields['weekday']:
#                         base = date
#                         break
#             else:
#                 raise ValueError('Can\'t find previous run time for date %s' % base)
#         else:
#             base = datetime.datetime(base.year, base.month, prev_day, base.hour, base.minute)
#         return base

#     def prev_run(self, time = datetime.datetime.now()):
#         """Calculates when the previous execution was."""
#         base = self.matches(time) and time or self.next_run(time)
#         # minute
#         prev_minute, carry = self.__prev_time(self.fields['minute'], base.minute)
#         min_diff = datetime.timedelta(minutes=(base.minute - prev_minute))
#         base -= min_diff
#         if not carry :
#             return base

#         # hour
#         prev_hour, carry = self.__prev_time(self.fields['hour'], base.hour)
#         hour_diff = datetime.timedelta(hours=(base.hour - prev_hour))
#         base -= hour_diff
#         if not carry :
#             return base

#         # day and weekday are strongly depend on month and year

#         prev_run = None
#         completed = False
#         prev_day, carry_day = self.__prev_time(self.fields['day'], base.day)
#         _carry_day = False
#         while 28 < prev_day and not _carry_day:
#             date = self.__prev_date(base, prev_day, carry_day)
#             if not prev_run or prev_run < date:
#                 prev_run = date
#             _prev_day = prev_day
#             prev_day, _carry_day = self.__prev_time(self.fields['day'], prev_day)
#             carry_day = carry_day or _carry_day
#         date = self.__prev_date(base, prev_day, carry_day)
#         if not prev_run or prev_run < date:
#             prev_run = date

#         return prev_run

#     def is_expired(self, time = datetime.datetime.now()):
#         """If the expiration parameter has been set this will check
#         wether too much time has been since the cron-entry. If the
#         expiration has not been set, it throws ValueError."""
#         if self.expiration == 0 :
#             raise ValueError("Missing argument",
#                              "Expiration time has not been set")
#         next_beg = self.next_run(time)
#         next_end = next_beg + self.expiration
#         prev_beg = self.prev_run(time)
#         prev_end = prev_beg + self.expiration
#         if (time >= next_beg and time <= next_end) or (time >= prev_beg and time <= prev_end) :
#             return False
#         return True



if __name__ == "__main__" :
	import datetime
	import unittest
	class CrontabTests( unittest.TestCase ):
		def setUp( self ):
			self.e = SimpleCrontabEntry()
		def tearDown( self ):
			self.e = None
		def datetimeToSeconds( self, datetimeIn ):
			return( (datetimeIn - datetime.datetime(1970,1,1)).total_seconds() )
		def test_instanceInitWithEntry( self ):
			self.e = None
			self.e = SimpleCrontabEntry("* * * * *")
			self.assertEqual( self.e.data, "* * * * *", "Given pattern is not stored in object." )
		def test_instanceInitWithoutEntry( self ):
			self.e = None
			self.e = SimpleCrontabEntry()
			self.assertIsNone( self.e.data, "This should still be None." )
		def test_set_value_noneResetsObject( self ):
			self.e.set_value("* * * * *")
			self.e.set_value(None)
			self.assertRaises( AttributeError, self.e.matches )
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
			self.assertTrue( self.e.matches( self.datetimeToSeconds( datetime.datetime(1970, 6, 10, 8, 30) ) ), "This should match." )
		def test_matches_specificDayTime_seconds_int( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertTrue( self.e.matches( 13854600 ) )
		def test_matches_specificDayTime_datetime( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertTrue( self.e.matches( datetime.datetime( 1970, 6, 10, 8, 30 ) ), "This should match." )
		def test_matches_specificDayTime_seconds_false( self ):
			self.e.set_value('30 8 10 6 *')
			self.assertFalse( self.e.matches( self.datetimeToSeconds( datetime.datetime(1970, 6, 10, 8, 31) ) ) )
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
		def test_next_run_timeBeforeMatch_01( self ):
			self.e.set_value('30 8 10 6 *')



	"""


``next_run`` method testing:



>>> e = SimpleCrontabEntry('30 8 10 6 *')

>>> e.next_run(datetime(1970, 1, 1))
datetime.datetime(1970, 6, 10, 8, 30)
>>> e.next_run(datetime(1970, 4, 1))
datetime.datetime(1970, 6, 10, 8, 30)

>>> e.next_run(datetime(1970, 6, 1))
datetime.datetime(1970, 6, 10, 8, 30)
>>> e.next_run(datetime(1970, 6, 6))
datetime.datetime(1970, 6, 10, 8, 30)

>>> e.next_run(datetime(1970, 6, 10))
datetime.datetime(1970, 6, 10, 8, 30)
>>> e.next_run(datetime(1970, 6, 10, 4))
datetime.datetime(1970, 6, 10, 8, 30)

>>> e.next_run(datetime(1970, 6, 10, 8))
datetime.datetime(1970, 6, 10, 8, 30)
>>> e.next_run(datetime(1970, 6, 10, 8, 15))
datetime.datetime(1970, 6, 10, 8, 30)

>>> e.next_run(datetime(1970, 6, 10, 8, 30))
datetime.datetime(1971, 6, 10, 8, 30)

>>> e = SimpleCrontabEntry('0 11,16 * * *')

>>> e.next_run(datetime(1970, 1, 1))
datetime.datetime(1970, 1, 1, 11, 0)
>>> e.next_run(datetime(1970, 1, 1, 14, 30))
datetime.datetime(1970, 1, 1, 16, 0)

>>> e = SimpleCrontabEntry('0 9-18 * * *')

>>> e.next_run(datetime(1970, 1, 1, 19))
datetime.datetime(1970, 1, 2, 9, 0)
>>> e.next_run(datetime(1970, 1, 1, 14, 30))
datetime.datetime(1970, 1, 1, 15, 0)

>>> e = SimpleCrontabEntry('0 9-18 * * 1-5')

>>> e.next_run(datetime(1970, 1, 1, 11)) # 1/1/1970 is Thursday.
datetime.datetime(1970, 1, 1, 12, 0)
>>> e.next_run(datetime(1970, 1, 3, 14, 30)) # 1/3/1970 is Saturday.
datetime.datetime(1970, 1, 5, 9, 0)

>>> e = SimpleCrontabEntry('* * * * *')

>>> e.next_run(datetime(1970, 1, 1))
datetime.datetime(1970, 1, 1, 0, 1)
>>> e.next_run(datetime(1970, 1, 1, 14, 30))
datetime.datetime(1970, 1, 1, 14, 31)

>>> e = SimpleCrontabEntry('0-10/2 * * * *')

>>> e.next_run(datetime(1970, 1, 1))
datetime.datetime(1970, 1, 1, 0, 2)
>>> e.next_run(datetime(1970, 1, 1, 14, 5))
datetime.datetime(1970, 1, 1, 14, 6)



``prev_run`` method testing:



>>> e = SimpleCrontabEntry('30 8 10 6 *')

>>> e.prev_run(datetime(1970, 1, 1))
datetime.datetime(1969, 6, 10, 8, 30)
>>> e.prev_run(datetime(1970, 6, 10, 8, 30))
datetime.datetime(1969, 6, 10, 8, 30)

>>> e = SimpleCrontabEntry('* 5 * * *')

>>> e.prev_run(datetime(1970, 4, 1))
datetime.datetime(1970, 3, 31, 5, 59)

>>> e = SimpleCrontabEntry('0 11,16 * * *')

>>> e.prev_run(datetime(1970, 1, 1))
datetime.datetime(1969, 12, 31, 16, 0)
>>> e.prev_run(datetime(1970, 1, 1, 13, 30))
datetime.datetime(1970, 1, 1, 11, 0)

>>> e = SimpleCrontabEntry('0 9-18 * * *')

>>> e.prev_run(datetime(1970, 1, 1, 19))
datetime.datetime(1970, 1, 1, 18, 0)
>>> e.prev_run(datetime(1970, 1, 1, 14, 30))
datetime.datetime(1970, 1, 1, 14, 0)

>>> e = SimpleCrontabEntry('* * * * *')

>>> e.prev_run(datetime(1970, 1, 1))
datetime.datetime(1969, 12, 31, 23, 59)
>>> e.prev_run(datetime(1970, 1, 1, 14, 30))
datetime.datetime(1970, 1, 1, 14, 29)

>>> e = SimpleCrontabEntry('0-10/2 * * * *')

>>> e.prev_run(datetime(1970, 1, 1))
datetime.datetime(1969, 12, 31, 23, 10)
>>> e.prev_run(datetime(1970, 1, 1, 14, 8))
datetime.datetime(1970, 1, 1, 14, 6)

>>> e = SimpleCrontabEntry('* 5 * * *')

>>> e.prev_run(datetime(1970, 5, 1))
datetime.datetime(1970, 4, 30, 5, 59)

>>> e = SimpleCrontabEntry('2,3,5,7 10 29 2 *')

>>> e.prev_run(datetime(1970, 1, 1)) # 1968 is the nearest leap-year.
datetime.datetime(1968, 2, 29, 10, 7)



``empty`` instantiation throws exceptions on use



>>> e = None
>>> e = SimpleCrontabEntry()

>>> e.matches()
Traceback (most recent call last):
	...
AttributeError: Crontab needs an entry to check against

>>> e.next_run()
Traceback (most recent call last):
	...
AttributeError: Crontab needs an entry to check against

>>> e.prev_run()
Traceback (most recent call last):
	...
AttributeError: Crontab needs an entry to check against



``empty`` instantiation works if entry is set



>>> e = None
>>> e = SimpleCrontabEntry()

>>> e.set_value('30 8 10 6 *')
>>> e.matches(datetime(1970, 6, 10, 8, 30))
True

>>> e.set_value('0 9-18 * * 1-5')
>>> e.next_run(datetime(1970, 1, 1, 11)) # 1/1/1970 is Thursday.
datetime.datetime(1970, 1, 1, 12, 0)

>>> e.set_value('* 5 * * *')
>>> e.prev_run(datetime(1970, 5, 1))
datetime.datetime(1970, 4, 30, 5, 59)



``set_value(None)`` clears the entry



>>> e = None
>>> e = SimpleCrontabEntry('* * * * *')
>>> e.set_value()

>>> e.matches()
Traceback (most recent call last):
	...
AttributeError: Crontab needs an entry to check against

>>> e.next_run()
Traceback (most recent call last):
	...
AttributeError: Crontab needs an entry to check against

>>> e.prev_run()
Traceback (most recent call last):
	...
AttributeError: Crontab needs an entry to check against

```Weekly when match day is last day of a 31 day month```

>>> e = None
>>> e = SimpleCrontabEntry('0 20 * * 3')	# 8pm on Wednesday

>>> e.next_run(datetime(2016, 8, 24, 20, 00)) # 24 Aug 2016, 20:01, next Wed should be 31 Aug
datetime.datetime(2016, 8, 31, 20, 0)

>>> e.next_run(datetime(2016, 8, 31, 20, 01)) # 31 Aug 2016, next Wednesday should be the 7 Sep
datetime.datetime(2016, 9, 7, 20, 0)

>>> e.next_run(datetime(2016, 11, 30, 20, 01)) # 30 Nov 2016, next Wednesday should be 7 Dec
datetime.datetime(2016, 12, 7, 20, 0)

"""

	unittest.main()
