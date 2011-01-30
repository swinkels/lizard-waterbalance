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
# Initial date:       2011-01-26
#
#******************************************************************************

from datetime import datetime
from unittest import TestCase

from lizard_waterbalance.level_control_storage import LevelControlStorage
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.timeseriesstub import TimeseriesStub

class LevelControlStorageTests(TestCase):

    def create_pumping_station(self, into=None, computed_level_control=None, percentage=None):
        """Create, store and return a new PumpingStation.

        Parameters:
        * into -- holds iff if the pumping station is an intake
        * computed_level_control -- holds if the pumping station can be used for level control
        * percentage -- percentage of all volume for this pumping station

        """
        pumping_station = PumpingStation()
        pumping_station.into = into
        pumping_station.computed_level_control = computed_level_control
        pumping_station.percentage = percentage
        pumping_station.save()
        return pumping_station

    def test_a(self):
        """Test the case that both time series are empty."""
        level_control = (TimeseriesStub(), TimeseriesStub())
        pumping_station = PumpingStation()
        pumping_station.into = True
        pumping_station.computed_level_control = True
        pumping_station.percentage = 100
        pumping_station.save()
        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        # we retrieve the pumping station from the database
        pk = pumping_station.pk
        pumping_station = PumpingStation.objects.get(pk=pk)

        self.assertEqual([], list(pumping_station.level_control.volume.events()))

    def test_b(self):
        """Test the case that only the outgoing time series is empty.

        There is one intake available for level control.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub())
        pumping_station = PumpingStation()
        pumping_station.into = True
        pumping_station.computed_level_control = True
        pumping_station.percentage = 100
        pumping_station.save()
        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        # we retrieve the pumping station from the database
        pk = pumping_station.pk
        pumping_station = PumpingStation.objects.get(pk=pk)

        expected_events = [(today, 10.0)]
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

    def test_ba(self):
        """Test the case that only the outgoing time series is empty.

        There are two intakes available for level control.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub())
        pumping_stations = [self.create_pumping_station(into=True, computed_level_control=True, percentage=10.0),
                            self.create_pumping_station(into=True, computed_level_control=True, percentage=90.0)]

        storage = LevelControlStorage()
        storage.store(level_control, pumping_stations)

        # we retrieve the first intake from the database
        pumping_station = PumpingStation.objects.get(pk=pumping_stations[0].pk)
        expected_events = [(today, 1.0)]
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

        # we retrieve the second intake from the database
        pumping_station = PumpingStation.objects.get(pk=pumping_stations[1].pk)
        expected_events = [(today, 9.0)]
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

    def test_c(self):
        """Test no WaterbalanceTimeserie is created for a pumping station without level control.

        There is an intake available but not for level control.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub())
        pumping_station = PumpingStation()
        pumping_station.into = True
        pumping_station.computed_level_control = False
        pumping_station.percentage = 100
        pumping_station.save()

        self.assertTrue(pumping_station.level_control is None)

        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        self.assertTrue(pumping_station.level_control is None)

    def test_d(self):
        """Test the case that only the outgoing time series is empty.

        There is no intake available.

        """

        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub())
        pumping_station = PumpingStation()
        pumping_station.into = False
        pumping_station.computed_level_control = True
        pumping_station.percentage = 100
        pumping_station.save()
        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        # we retrieve the pumping station from the database
        pk = pumping_station.pk
        pumping_station = PumpingStation.objects.get(pk=pk)

        expected_events = []
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

    def test_e(self):
        """Test the case that both incoming and outgoing time series contain events.

        There is only a single pump available.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub((today, 20.0)))
        pumping_station = PumpingStation()
        pumping_station.into = False
        pumping_station.computed_level_control = True
        pumping_station.percentage = 100
        pumping_station.save()
        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        # we retrieve the pumping station from the database
        pk = pumping_station.pk
        pumping_station = PumpingStation.objects.get(pk=pk)

        expected_events = [(today, 20.0)]
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

    def test_f(self):
        """Test the case that both incoming and outgoing time series contain events.

        There is a single intake available and a single pump.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub((today, -20.0)))
        pumping_station = PumpingStation()
        pumping_station.into =  True
        pumping_station.computed_level_control = True
        pumping_station.percentage = 100
        pumping_station.save()
        intake_pk = pumping_station.pk
        pumping_stations = [pumping_station]
        pumping_station = PumpingStation()
        pumping_station.into = False
        pumping_station.computed_level_control = True
        pumping_station.percentage = 100
        pumping_station.save()
        pump_pk = pumping_station.pk
        pumping_stations.append(pumping_station)

        storage = LevelControlStorage()
        storage.store(level_control, pumping_stations)

        # we retrieve the intake pumping station from the database
        pumping_station = PumpingStation.objects.get(pk=intake_pk)
        expected_events = [(today, 10.0)]
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

        # we retrieve the pump pumping station from the database
        pumping_station = PumpingStation.objects.get(pk=pump_pk)
        expected_events = [(today, -20.0)]
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

    def test_g(self):
        """Test that the WaterbalanceTimeserie of a PumpingStation is only created once.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub())
        pumping_station = self.create_pumping_station(into=True, computed_level_control=True, percentage=10.0)
        intake_pk = pumping_station.pk

        self.assertTrue(pumping_station.level_control is None)

        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        self.assertFalse(pumping_station.level_control is None)
        level_control_pk = pumping_station.level_control.pk

        storage.store(level_control, [pumping_station])

        # we retrieve the pump pumping station from the database
        pumping_station = PumpingStation.objects.get(pk=intake_pk)
        self.assertEqual(level_control_pk, pumping_station.level_control.pk)

    def test_h(self):
        """Test the case that only the outgoing time series is empty.

        There is an intake available but not for level control.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub())
        pumping_station = PumpingStation()
        pumping_station.into = True
        pumping_station.computed_level_control = True
        pumping_station.percentage = 100
        pumping_station.save()
        intake_pk = pumping_station.pk

        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        self.assertFalse(pumping_station.level_control is None)

        pumping_station.computed_level_control = False
        pumping_station.percentage = 100
        pumping_station.save()

        storage.store(level_control, [pumping_station])

        # we retrieve the pumping station from the database
        pumping_station = PumpingStation.objects.get(pk=intake_pk)

        expected_events = []
        self.assertEqual(expected_events, list(pumping_station.level_control.volume.events()))

    def test_i(self):
        """Test that the number of Timeseries does not increase when one is recomputed.

        """
        today = datetime(2011, 1, 26)
        level_control = (TimeseriesStub((today, 10.0)), TimeseriesStub())
        pumping_station = self.create_pumping_station(into=True, computed_level_control=True, percentage=10.0)

        storage = LevelControlStorage()
        storage.store(level_control, [pumping_station])

        expected_timeseries_count = Timeseries.objects.count()

        storage.store(level_control, [pumping_station])

        self.assertEqual(expected_timeseries_count, Timeseries.objects.count())