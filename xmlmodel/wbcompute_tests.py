#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The xml package provides the functionality to calculate the waterbalance for
# a waterbalance configuration specified in set of XML files.
#
# Copyright (C) 2011 Nelen & Schuurmans
#
# This package is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this package.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
from unittest import TestCase
from xml.dom.minidom import parseString

from mock import Mock

from nens import mock as nens_mock
from timeseries.timeseriesstub import TimeseriesStub
from timeseries.timeseriesstub import SparseTimeseriesStub
from xmlmodel.reader import Area
from xmlmodel.wbcompute import insert_calculation_range
from xmlmodel.wbcompute import FractionsTimeseries
from xmlmodel.wbcompute import TimeSeriesSpec
from xmlmodel.wbcompute import TimeseriesForLabel
from xmlmodel.wbcompute import Units
from xmlmodel.wbcompute import WriteableTimeseriesList


def create_station():
    station = Mock()
    station.location_id = 20111121
    return station


class Tests(TestCase):

    def setUp(self):

        run_file_contents = '''\
<?xml version="1.0" encoding="UTF-8"?>
<Run xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.wldelft.nl/fews/PI" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_run.xsd" version="1.5">
    <timeZone>1.0</timeZone>
    <startDateTime date="2004-12-23" time="00:00:00"/>
    <endDateTime date="2011-11-16" time="00:00:00"/>
    <time0 date="2010-01-01" time="00:00:00"/>
    <workDir>data/Waterbalans/model</workDir>
    <inputParameterFile>data/deltares/input/Parameters.xml</inputParameterFile>
    <inputTimeSeriesFile>data/deltares/input/Tijdreeksen.xml</inputTimeSeriesFile>
    <outputDiagnosticFile>data/deltares/output/Diagnostics.xml</outputDiagnosticFile>
    <outputTimeSeriesFile>data/deltares/output/waterbalance-graph.xml</outputTimeSeriesFile>
    <properties>
        <string key="Regio" value="Waternet"/>
        <string key="Gebied" value="SAP"/>
    </properties>
</Run>
'''
        self.run_dom = parseString(run_file_contents)

    def test(self):
        """Function insert_calculation_range inserts the right start and end datetime."""
        run_info = {}
        insert_calculation_range(self.run_dom, run_info)
        self.assertEqual(datetime(2004, 12, 23), run_info['startDateTime'])
        self.assertEqual(datetime(2011, 11, 16), run_info['endDateTime'])

    def test_b(self):
        """Test the requirements for a TimeseriesStub to be writeable."""
        stream = nens_mock.Stream()
        timeseries = TimeseriesStub((datetime(2011, 11, 17), 10.0))
        timeseries.type = 'instantaneous'
        timeseries.location_id = 'SAP'
        timeseries.parameter_id = 'Q'
        timeseries.miss_val = '-999.0'
        timeseries.station_name = 'Huh?'
        timeseries.units = 'dag'
        TimeseriesStub.write_to_pi_file(stream, [timeseries])

    def test_c(self):
        """Test the requirements for a SparseTimeseriesStub to be writeable."""
        stream = nens_mock.Stream()
        timeseries = SparseTimeseriesStub(datetime(2011, 11, 17), [10.0])
        timeseries.type = 'instantaneous'
        timeseries.location_id = 'SAP'
        timeseries.parameter_id = 'Q'
        timeseries.miss_val = '-999.0'
        timeseries.station_name = 'Huh?'
        timeseries.units = 'dag'
        SparseTimeseriesStub.write_to_pi_file(stream, [timeseries])


class MoreTests(TestCase):

    def setUp(self):
        self.area = Area()
        self.area.location_id = 20111117
        self.label2spec = {'hardened': TimeSeriesSpec('discharge_hardened', Units.flow)}

    def test_a(self):
        writeable_timeseries = \
            WriteableTimeseriesList(self.area, self.label2spec)

        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'hardened': timeseries})

        self.assertEqual(1, len(writeable_timeseries.timeseries_list))

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(timeseries, single_timeseries)

    def test_ba(self):
        """Test the right location is assigned."""
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'hardened': timeseries})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(20111117, single_timeseries.location_id)

    def test_bb(self):
        """Test the right parameter is assigned."""
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'hardened': timeseries})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual('discharge_hardened', single_timeseries.parameter_id)

    def test_bc(self):
        """Test the right unit is assigned."""
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'hardened': timeseries})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(Units.flow, single_timeseries.units)

    def test_bd(self):
        """Test the default right parameters are assigned."""
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'hardened': timeseries})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual('instantaneous', single_timeseries.type)
        self.assertEqual('-999.0', single_timeseries.miss_val)
        self.assertEqual('unspecified', single_timeseries.station_name)

    def test_c(self):
        """Test an empty dict of PumpingStation to TimeseriesStub."""
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                       self.label2spec)

        writeable_timeseries.insert({'defined_input': {}})

        self.assertEqual(0, len(writeable_timeseries.timeseries_list))

    def test_d(self):
        """Test a dict of PumpingStation to TimeseriesStub of size 1."""
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        station = create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'defined_input': {station: timeseries}})

        self.assertEqual(1, len(writeable_timeseries.timeseries_list))
        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(timeseries, single_timeseries)

    def test_e(self):
        """Test the right location id is assigned.

        The writeable time series should have a location id equal to
        the location id of the pumping station.

        """
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        station = create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'defined_input': {station: timeseries}})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(20111121, single_timeseries.location_id)

    def test_f(self):
        """Test the right parameter id is assigned.

        The writeable time series should have parameter id 'Q'.

        """
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        station = create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'defined_input': {station: timeseries}})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual('Q', single_timeseries.parameter_id)

    def test_g(self):
        """Test the right units are assigned.

        The writeable time series should have units Units.flow.

         """
        writeable_timeseries = WriteableTimeseriesList(self.area,
                                                   self.label2spec)

        station = create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'defined_input': {station: timeseries}})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(Units.flow, single_timeseries.units)

class WriteableTimeseriesListTests(TestCase):

    def setUp(self):
        self.area = Area()
        self.area.location_id = 20111208
        self.label2spec = {'min_impact_phosphate_discharge': TimeSeriesSpec('min_impact_phosphate_discharge', Units.impact)}

    def test_a(self):
        """Test the insert of an empty mapping."""
        writeable_timeseries = WriteableTimeseriesList(self.area, self.label2spec)
        writeable_timeseries.insert({})
        self.assertEqual([], writeable_timeseries.timeseries_list)

    def test_b(self):
        """Test the insert of an empty mapping of 'intakes' time series."""
        writeable_timeseries = WriteableTimeseriesList(self.area, self.label2spec)
        writeable_timeseries.insert({'intakes': ("min_impact_phosphate_discharge" ,{})})
        self.assertEqual([], writeable_timeseries.timeseries_list)

    def test_c(self):
        """Test the insert of a mapping of a single 'intakes' time series."""
        writeable_timeseries = WriteableTimeseriesList(self.area, self.label2spec)

        intake = create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'intakes': ("min_impact_phosphate_discharge", {intake: timeseries})})

        self.assertEqual(1, len(writeable_timeseries.timeseries_list))

        single_timeseries = writeable_timeseries.timeseries_list[0]

        self.assertEqual(intake.location_id, single_timeseries.location_id)
        self.assertEqual("min_impact_phosphate_discharge", single_timeseries.parameter_id)
        self.assertEqual(Units.impact, single_timeseries.units)


class FractionsTimeseries_as_writeable_timeseries_TestSuite(TestCase):

    def setUp(self):
        self.area_location = 20120124
        self.fractions = FractionsTimeseries(self.area_location)

    def test_a(self):
        """Test an empty dictionary."""
        multiple_timeseries = self.fractions.as_writeables({})
        self.assertEqual([], multiple_timeseries)

    def test_b(self):
        """Test a dictionary of a single time series.

        The time series is not the discharge time series of a pumping station.

        """
        timeseries = SparseTimeseriesStub()
        writeables = self.fractions.as_writeables({'initial': timeseries})
        expected_writeables = \
            [self._expected_writeable(timeseries, self.area_location,
                                      'fraction_water_initial')]
        self.assertEqual(expected_writeables, writeables)

    def _expected_writeable(self, timeseries, location, parameter):
        units = Units.fraction
        return TimeseriesForLabel(timeseries, location, parameter, units)

    def test_c(self):
        """Test a dictionary of multiple time series.

        The multiple time series are not the discharge time series of pumping
        stations.

        """
        initial_timeseries = SparseTimeseriesStub()
        seepage_timeseries = SparseTimeseriesStub()
        writeables = \
          self.fractions.as_writeables({'initial': initial_timeseries,
                                        'seepage': seepage_timeseries})
        expected_writeables = \
          [self._expected_writeable(initial_timeseries, self.area_location,
                                    'fraction_water_initial'),
           self._expected_writeable(seepage_timeseries, self.area_location,
                                    'fraction_water_seepage')]
        self.assertTrue(self._writeables_are_equal(expected_writeables, writeables))

    def _writeables_are_equal(self, writeables, other_writeables):
        for writeable in writeables:
            if not writeable in other_writeables:
                return False
        for writeable in other_writeables:
            if not writeable in writeables:
                return False
        return True

    def test_d(self):
        """Test a dictionary of a single time series.

        The time series is the discharge time series of a pumping station that
        is not used for level control.

        """
        intake = self._create_intake(location='Wijchen', is_computed=False)
        timeseries = SparseTimeseriesStub()
        writeables = \
             self.fractions.as_writeables({'intakes': {intake: timeseries}})
        expected_writeables = \
            [self._expected_writeable(timeseries, 'Wijchen',
                                      'fraction_water_discharge')]
        self.assertEqual(expected_writeables, writeables)

    def _create_intake(self, location, is_computed):
        intake = Mock()
        intake.location_id = location
        intake.is_computed = is_computed
        return intake

    def test_e(self):
        """Test a dictionary of multiple time series.

        The multiple time series are the discharge time series of pumping
        stations that are not used for level control.

        """
        intakes = [self._create_intake(location=location, is_computed=False)
                   for location in ['Wijchen', 'Utrecht']]
        label2intakes = {intakes[0]: SparseTimeseriesStub(),
                         intakes[1]: SparseTimeseriesStub()}
        writeables = \
            self.fractions.as_writeables({'intakes': label2intakes})
        expected_writeables = \
            [self._expected_writeable(SparseTimeseriesStub(), 'Wijchen',
                                      'fraction_water_discharge'),
             self._expected_writeable(SparseTimeseriesStub(), 'Utrecht',
                                      'fraction_water_discharge')]
        self.assertTrue(self._writeables_are_equal(expected_writeables,
                                                   writeables))

    def test_f(self):
        """Test a dictionary of a single time series.

        The time series is the discharge time series of a pumping station that
        is used for level control.

        """
        intake = self._create_intake(location='Wijchen', is_computed=True)
        timeseries = SparseTimeseriesStub()
        writeables = \
            self.fractions.as_writeables({'intakes': {intake: timeseries}})
        expected_writeables = \
            [self._expected_writeable(timeseries, 'Wijchen',
                                      'fraction_water_level_control')]
        self.assertEqual(expected_writeables, writeables)
