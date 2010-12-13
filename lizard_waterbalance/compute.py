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
# Initial date:       2010-11-26
#
#******************************************************************************

from lizard_waterbalance.timeseriesstub import add_timeseries
from lizard_waterbalance.timeseriesstub import multiply_timeseries
from lizard_waterbalance.timeseriesstub import TimeseriesStub

class BucketOutcome:
    """Stores the time series that are computed for a Bucket.

    Instance variables:
    * storage -- time series for *berging*
    * flow_off -- time series for *afstroming*
    * net_drainage -- time series for *drainage* and *intrek*
    * seepage -- time series for *kwel*

    The value of a net_drainage event is positive when there is water coming
    into the bucket and negatice when there is water going out of the bucket.

    """
    def __init__(self):

        self.storage = TimeseriesStub(0)
        self.flow_off = TimeseriesStub(0)
        self.net_drainage = TimeseriesStub(0)
        self.seepage = TimeseriesStub(0)
        self.net_precipitation = TimeseriesStub(0)

    def name2timeseries(self):
        return {"storage": self.storage,
                "flow_off": self.flow_off,
                "net_drainage": self.net_drainage,
                "seepage": self.seepage,
                "net_precipitation": self.net_precipitation}

class OpenWaterOutcome:
    """Stores the time series that are computed for an OpenWater.

    Instance variables:
    * precipitation -- time series for *neerslag*
    * evaporation -- time series for *verdamping*

    """
    def __init__(self):
        self.precipitation = TimeseriesStub(0)
        self.evaporation = TimeseriesStub(0)
        self.seepage = TimeseriesStub(0)

    def name2timeseries(self):
        return {"precipitation": self.precipitation,
                "evaporation": self.evaporation,
                "seepage": self.seepage}

def compute_seepage(bucket, seepage):
    """Return the seepage of the given bucket on the given date.

    Parameters:
    * bucket -- bucket for which to compute the seepage
    * date -- date for which to compute the seepage
    * seepage -- seepage in [mm/day]

    """
    # with regard to the factor 0.001 in the next line, seepage is specified
    # in [mm/day] but surface in [m]: 1 [mm] == 0.001 [m]
    return (bucket.surface * seepage) / 1000.0


def compute_net_precipitation(bucket,
                              previous_volume,
                              precipitation,
                              evaporation):
    """Return the net precipitation of today.

    With net precipitation, we mean the volume difference caused by
    precipitation and evaporation.

    Parameters:
    * bucket -- bucket for which to compute the net precipitation
    * previous_volume -- water volume of the bucket the day before
    * precipitation -- precipitation of today in [mm/day]
    * evaporation -- evaporation of today in [mm/day]

    """
    equi_volume = bucket.equi_water_level * bucket.surface
    if previous_volume > equi_volume:
        evaporation_factor = bucket.crop_evaporation_factor
    else:
        evaporation_factor = bucket.min_crop_evaporation_factor

    net_precipitation = precipitation - evaporation * evaporation_factor
    # with regard to the factor 0.001 in the next line, precipitation and
    # evaporation are specified in [mm/day] but surface in [m]: 1 [mm] == 0.001
    # [m]
    return net_precipitation * bucket.surface / 1000.0


def compute_net_drainage(bucket, previous_volume):
    """Return the net drainage of today.

    With net drainage, we mean the volume difference caused by drainage and
    infiltration.

    Parameters:
    * bucket -- bucket for which to compute the net drainage
    * previous_volume -- water volume of the bucket the day before

    """
    equi_volume = bucket.equi_water_level * bucket.surface
    if previous_volume > equi_volume:
        net_drainage = -previous_volume * bucket.drainage_fraction
    elif previous_volume < equi_volume:
        net_drainage = -previous_volume * bucket.infiltration_fraction
    else:
        net_drainage = 0
    return net_drainage

def compute(bucket, previous_volume, precipitation, evaporation, seepage):
    """Compute and return the waterbalance of the given bucket.

    This method computes the water level, flow off and net drainage of the
    given bucket and returns them as a triple.

    Parameters:
    * bucket -- bucket for which to compute the waterbalance
    * previous_volume -- water volume of the bucket the day before
    * precipitation -- precipitation for the bucket in [mm/day]
    * evaporation -- evaporation for the bucket in [mm/day]
    * seepage -- seepage for the bucket in [mm/day]

    """
    max_volume = bucket.max_water_level * bucket.porosity * bucket.surface

    Q_precipitation = compute_net_precipitation(bucket,
                                                previous_volume,
                                                precipitation,
                                                evaporation)
    Q_seepage = compute_seepage(bucket, seepage)
    Q_drain = compute_net_drainage(bucket, previous_volume)
    Q_in = Q_drain + Q_precipitation + Q_seepage

    if previous_volume + Q_in < max_volume:
        volume = previous_volume + Q_in
        Q_afst = 0
    else:
        volume = max_volume
        Q_afst = -(previous_volume + Q_in - max_volume)

    return (volume, Q_afst, Q_drain, Q_seepage, Q_precipitation)

def enumerate_events(precipitation, evaporation, seepage):

    for triple in zip(precipitation.events(), evaporation.events(), seepage.events()):
        latest_start_date = triple[0][0]
        if latest_start_date < triple[1][0]:
            latest_start_date = triple[1][0]
        if latest_start_date < triple[2][0]:
            latest_start_date = triple[2][0]
        break

    precipitation = (event for event in precipitation.events() if event[0] >= latest_start_date)
    evaporation = (event for event in evaporation.events() if event[0] >= latest_start_date)
    seepage = (event for event in seepage.events() if event[0] >= latest_start_date)

    for triple in zip(precipitation, evaporation, seepage):
        yield triple

def compute_timeseries(bucket, precipitation, evaporation, seepage, compute):
    """Compute and return the waterbalance time series of the given bucket.

    This method computes the time series that can be stored in a BucketOutcome
    for the given bucket and returns these times series as a BucketOutcome.

    Parameters:
    * bucket -- undrained surface for which to compute the waterbalance
    * precipitation -- precipitation time series in [mm/day]
    * evaporation -- evaporation time series  in [mm/day]
    * seepage -- seepage time series in [mm/day]
    * compute -- function to compute the daily waterbalance

    """
    outcome = BucketOutcome()
    volume = bucket.init_water_level * bucket.surface
    for triple in enumerate_events(precipitation, evaporation, seepage):
        precipitation_event = triple[0]
        event_date = precipitation_event[0]
        evaporation_event = triple[1]
        seepage_event = triple[2]
        bucket_triple = compute(bucket, volume, precipitation_event[1],
                                evaporation_event[1], seepage_event[1])
        #note that bucket_triple is a quintuple now
        volume = bucket_triple[0]
        outcome.storage.add_value(event_date, volume)
        outcome.flow_off.add_value(event_date, bucket_triple[1])
        outcome.net_drainage.add_value(event_date, bucket_triple[2])
        outcome.seepage.add_value(event_date, bucket_triple[3])
        outcome.net_precipitation.add_value(event_date, bucket_triple[4])
    return outcome

def compute_timeseries_on_hardened_surface(bucket, precipitation, evaporation, seepage, compute):

    # we first compute the upper bucket:
    #   - the upper bucket does not have seepage and does not have net drainage
    #   - the porosity of the upper bucket is always 1.0
    upper_seepage = TimeseriesStub(0)
    bucket.porosity, tmp = 1.0, bucket.porosity
    upper_outcome = compute_timeseries(bucket,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       compute)
    bucket.porosity = tmp

    # we then compute the lower bucket:
    #  - the lower bucket does not have precipitation, evaporation and does not
    #    have flow off
    lower_precipitation = TimeseriesStub(0)
    lower_evaporation = TimeseriesStub(0)
    lower_outcome = compute_timeseries(bucket,
                                       lower_precipitation,
                                       lower_evaporation,
                                       seepage,
                                       compute)

    outcome = BucketOutcome()
    outcome.storage = upper_outcome.storage
    outcome.flow_off = upper_outcome.flow_off
    outcome.net_drainage = lower_outcome.net_drainage
    outcome.seepage = lower_outcome.seepage
    outcome.net_precipitation = upper_outcome.net_precipitation
    return outcome

def compute_timeseries_on_drained_surface(bucket, precipitation, evaporation, seepage, compute):

    # we first compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the upper bucket has some of its own attributes
    upper_seepage = TimeseriesStub(0)

    bucket.porosity, bucket.upper_porosity = bucket.upper_porosity, bucket.porosity
    bucket.crop_evaporation_factor, buckets.upper_crop_evaporation_factor = buckets.upper_crop_evaporation_factor, bucket.crop_evaporation_factor
    bucket.min_crop_evaporation_factor, buckets.upper_min_crop_evaporation_factor = buckets.upper_min_crop_evaporation_factor, bucket.min_crop_evaporation_factor
    upper_outcome = compute_timeseries(bucket,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       compute)
    bucket.porosity, bucket.upper_porosity = bucket.upper_porosity, bucket.porosity
    bucket.crop_evaporation_factor, buckets.upper_crop_evaporation_factor = buckets.upper_crop_evaporation_factor, bucket.crop_evaporation_factor
    bucket.min_crop_evaporation_factor, buckets.upper_min_crop_evaporation_factor = buckets.upper_min_crop_evaporation_factor, bucket.min_crop_evaporation_factor

    # we then compute the lower bucket:
    #  - the lower bucket does not have precipitation, evaporation and does not
    #    have flow off
    lower_precipitation = add_timeseries(upper_flow_off, upper_net_drainage)
    lower_evaporation = TimeseriesStub(0)
    lower_outcome = compute_timeseries(bucket,
                                       lower_precipitation,
                                       lower_evaporation,
                                       seepage,
                                       compute)

    outcome = BucketOutcome()
    outcome.storage = upper_outcome.storage
    outcome.flow_off = upper_outcome.flow_off
    outcome.net_drainage = lower_outcome.net_drainage
    outcome.seepage = lower_outcome.seepage
    outcome.net_precipitation = upper_outcome.net_precipitation
    return outcome
    return (upper_storage,
            add_timeseries(upper_flow_off, lower_flow_off),
            add_timeseries(upper_net_drainage, lower_net_drainage))


def open_water_compute(open_water,
                       buckets,
                       bucket_computers,
                       pumping_stations,
                       timeseries_retriever):
    """Compute and return the waterbalance.

    Parameters:
    * open_water -- open water for which the function computes the waterbalance
    * buckets -- list of buckets connected to the open water
    * bucket_computers -- dictionary of bucket surface type to function
    * pumping_stations -- list of stations that pump water into or out of the open water
    * timeseries_retriever -- object to retrieve the input time series

    Return value:
    * result -- dictionary of bucket and open water name to time series name
    to time series

    The input time series are precipitation, evaporation and seepage.

    """
    result = {}

    precipitation = timeseries_retriever.get_timeseries("precipitation")
    evaporation = timeseries_retriever.get_timeseries("evaporation")
    seepage = timeseries_retriever.get_timeseries("seepage")

    for bucket in buckets:
        bucket_computer = bucket_computers[bucket.surface_type]
        outcome = bucket_computer(bucket, precipitation, evaporation, seepage, compute)
        print bucket, outcome
        result.setdefault(bucket.name, outcome)

    # [<open-water-name>]['precipitation'] to TimeseriesStub
    # [<open-water-name>]['evaporation'] to TimeseriesStub
    # [<open-water-name>]['sum hardened flow_off'] to TimeseriesStub
    # [<open-water-name>]['sum drained flow_off + net_drainage'] to TimeseriesStub
    # [<open-water-name>]['sum hardened net_drainage and undrained net_drainage'] to TimeseriesStub
    # [<open-water-name>]['sum undrained flow_off'] to TimeseriesStub
    # [<open-water-name>]['sum intake'] to TimeseriesStub
    # [<open-water-name>]['sum infiltration'] to TimeseriesStub
    # [<open-water-name>]['sum seepage'] to TimeseriesStub
    # [<open-water-name>]['sum sluice error'] to TimeseriesStub

    outcome = result.setdefault(open_water.name, OpenWaterOutcome())

    if precipitation:
        result[open_water.name].precipitation = multiply_timeseries(precipitation, open_water.surface / 1000.0)
    if evaporation:
        result[open_water.name].evaporation = multiply_timeseries(evaporation, -open_water.surface * open_water.crop_evaporation_factor / 1000.0)
    if seepage:
        result[open_water.name].seepage = multiply_timeseries(seepage, open_water.surface / 1000.0)

    return result
