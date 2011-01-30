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

from lizard_waterbalance.timeseries import store_waterbalance_timeserie


class VerticalTimeseriesStorage:

    def store(self, vertical_timeseries, open_water):
        """Computes and stores the vertical time series in the database.

        Parameters:
        * vertical_timeseries -- list of time series [precipitation,
          evaporation, seepage, infiltration], where each time series is
          specified in [m3/day]
        * open_water -- OpenWater that will contain the time series

        """
        names = ["precipitation", "evaporation", "seepage", "infiltration"]
        for index, name in enumerate(names):
            attribute_name = "computed_" + name
            timeseries = vertical_timeseries[index]
            store_waterbalance_timeserie(open_water, attribute_name, timeseries)
        open_water.save()