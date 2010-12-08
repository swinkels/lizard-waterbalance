#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Pieter Swinkels
# Initial date:       2010-11-24
#
#******************************************************************************

from datetime import datetime
from datetime import timedelta

from filereader import FileReader

class TimeseriesStub:
    """Represents a time series.

    A time series is a sequence of values ordered by date and time.

    Instance variables:
    * initial_value -- value on any date before the first date
    * events -- list of (date and time, value) tuples ordered by date and time

    """
    def __init__(self, initial_value):
        self.initial_value = initial_value
        self._events = []

    def get_value(self, date_time):
        """Return the value on the given date and time.

        Note that this method assumes that the events are ordered earliest date
        and time first.

        """
        values = (event[1] for event in self._events if date_time >= event[0])
        return next(values, self.initial_value)

    def add_value(self, date_time, value):
        """Add the given value for the given date and time.

        Please note that events should be added earliest date and time first.

        """
        self._events.append((date_time, value))

    def events(self):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function fills
        in the missing dates with value 0.

        """
        previous_value = None
        date_to_yield = None # we initialize this variable to silence pyflakes
        for event in self._events:
            if previous_value:
                while date_to_yield < event[0]:
                    yield (date_to_yield, 0)
                    date_to_yield = date_to_yield + timedelta(1)
            yield event
            previous_value = event[1]
            date_to_yield = event[0] + timedelta(1)

    def monthly_events(self):
        """Return a generator to iterate over all monthly events.

        A TimeseriesStub stores daily events. This generator aggregates these
        daily events to monthly events that is placed at the first of the month
        and whose value is the total value of the daily events for that month.

        """
        current_year = None
        current_month = None
        current_value = 0
        for date, value in self.events():
            if current_month:
                if date.year == current_year and date.month == current_month:
                    current_value += value
                elif date.year > current_year or date.month > current_month:
                    yield datetime(current_year, current_month, 1), current_value
                    current_year = date.year
                    current_month = date.month
                    current_value = value
            else:
                current_year = date.year
                current_month = date.month
                current_value = value
        yield datetime(current_year, current_month, 1), current_value

    def __eq__(self, other):
        """Return True iff the two given time series represent the same events."""
        my_events = list(self.events())
        your_events = list(other.events())
        equal = len(my_events) == len(your_events)
        if equal:
            for (my_event, your_event) in zip(my_events, your_events):
                equal = my_event == your_event
                if not equal:
                    break
        return equal

def add_timeseries(timeseries_a, timeseries_b):
    """Return the sum of the given time series.

    The product is a TimeseriesStub.

    """
    sum = TimeseriesStub(0)
    for (a, b) in zip(timeseries_a.events(), timeseries_b.events()):
        sum.add_value(a[0], a[1] + b[1])
    return sum

def multiply_timeseries(timeseries, value):
    """Return the product of the given time series with the given value.

    The product is a TimeseriesStub.

    """
    product = TimeseriesStub(0)
    for event in timeseries.events():
        product.add_value(event[0], event[1] * value)
    return product

def split_timeseries(timeseries):
    """Return the 2-tuple of non-positive and non-negative time series.

    Paramaters:
    * timeseries -- time series that contains the events for the new 2 -tuple

    This function creates a 2-tuple of TimeseriesStub, where the first element
    contains all non-positive events (of the given time series) and the second
    element contains all non-negative events. The 2 resulting time series have
    events for the same dates as the given time series, but with value zero if
    the value at that date does not have the right sign.

    """
    non_pos_timeseries = TimeseriesStub(0)
    non_neg_timeseries = TimeseriesStub(0)
    for (date, value) in timeseries.events():
        if value > 0:
            non_pos_timeseries.add_value(date, 0)
            non_neg_timeseries.add_value(date, value)
        elif value < 0:
            non_pos_timeseries.add_value(date, value)
            non_neg_timeseries.add_value(date, 0)
        else:
            non_pos_timeseries.add_value(date, 0)
            non_neg_timeseries.add_value(date, 0)
    return (non_pos_timeseries, non_neg_timeseries)

def create_from_file(filename, filereader=FileReader()):
    """Return a dictionary from bucket and open water name to bucket and open water outcome."""
    result = {}
    filereader.open(filename)
    for line in filereader.readlines():
        name, label, year, month, day, value = line.split(',')
        date = datetime(int(year), int(month), int(day))
        value = float(value)
        result.setdefault(name, {})
        result[name].setdefault(label, TimeseriesStub(0))
        result[name][label].add_value(date, value)
    filereader.close()
    return result
