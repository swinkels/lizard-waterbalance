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
# Copyright 2011 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Pieter Swinkels
#
#******************************************************************************

from timeseries.timeseriesstub import enumerate_dict_events
from timeseries.timeseriesstub import multiply_timeseries
from timeseries.timeseriesstub import TimeseriesStub


class Load(object):

    def __init__(self, label):
        self.label = label
        self.name = label
        self.timeseries = TimeseriesStub()

    def multiply_timeseries(self, factor):
        self.timeseries = multiply_timeseries(self.timeseries, factor)

    def on_open_water_flow(self):
        return False


class LoadForOpenWaterFlow(Load):

    def __init__(self, label):
        super(LoadForOpenWaterFlow, self).__init__(label)
        self.name = self.label

    def on_open_water_flow(self):
        return True


class LoadForLabel(Load):

    def __init__(self, label):
        super(LoadForLabel, self).__init__(label)
        self.name = self.label

class LoadForIntake(Load):

    def __init__(self, intake):
        super(LoadForIntake, self).__init__(intake)
        self.name = intake.name


class LoadComputer:

    def compute(self, area, concentration_string, substance_string,
                flow_dict, concentration_dict,
                start_date, end_date, nutricalc_timeseries=None):
        """Compute and return the concentration time series.

        Parameters:
          *area*
            area for which to compute the load
          *concentration_string*
            either 'min' or 'incr'
          *substance_string*
            either 'phosphate' or 'nitrogen'
          *flow_list*
            dictionary of incoming waterflows
          *concentration_list*
            dict of label keys with concentration values in [mg/l]

        This method returns a dictionary of flow to time series. The flow can
        be (specified by) a string such as 'precipitation', 'seepage' or
        'drained', or can be (specified by) a PumpingStation.

        In an earlier version of this method the keys of the returned
        dictionary where always a string but that has been changed to solve the
        problem reported in ticket:2542.

        Remarks:
          * flows_dict['defined_input'] is a dictionary from intake to time
            series
          * this method would benefit from additional documentation and a
            review

        """

        self.loads = []

        if nutricalc_timeseries:
            flow_dict['nutricalc'] = nutricalc_timeseries

        for events in enumerate_dict_events(flow_dict):
            date = events['date']
            if date < start_date:
                continue
            if date >= end_date:
                break

            del(events['date'])

            if nutricalc_timeseries:
                del(events['drained'])
                del(events['undrained'])

            for key, value in events.items():
                if key in ['precipitation', 'seepage']:
                    label = key
                    attr_string = '%s_concentr_%s_%s' % \
                                  (concentration_string, substance_string, key)
                    load = value[1] * getattr(area, attr_string)
                    self._set_load(label, date, load)
                elif key in ['defined_input', 'intake_wl_control']:
                    for key_intake, value_intake in value.items():
                        label = key_intake
                        attr_string = '%s_concentr_%s' % \
                                      (concentration_string, substance_string)
                        load = value_intake[1] * getattr(key_intake, attr_string)
                        self._set_load(label, date, load)

        return self.loads

    def _set_load(self, label, date, value):
        load = next((load for load in self.loads if label == load.label), None)
        if load is None:
            if type(label) == str and label in ['precipitation', 'seepage']:
                load = LoadForOpenWaterFlow(label)
            elif type(label) == str:
                load = LoadForLabel(label)
            else:
                load = LoadForIntake(label)
            self.loads.append(load)
        load.timeseries.add_value(date, value)
