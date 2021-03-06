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

from lizard_wbcomputation.bucket_types import BucketTypes

from timeseries.timeseriesstub import SparseTimeseriesStub
from timeseries.timeseriesstub import enumerate_events


class BucketsSummary:
    """Stores the total time series computed for all buckets.

    Instance variables:
    * totals -- totals time series in [m3/day] of the other time series
    * hardened -- time series in [m3/day] for *Qsom verhard*
    * drained -- time series in [m3/day] for *Qsom gedraineerdonder*
    * undrained -- time series in [m3/day] for *Qsom ongedraineerd*
    * flow off -- time series in [m3/day] for *Qsom afst*
    * indraft -- time series in [m3/day] for *Qsom intrek*

    """
    def __init__(self):
        self.totals = SparseTimeseriesStub()
        self.total_incoming = SparseTimeseriesStub()
        self.total_outgoing = SparseTimeseriesStub()
        self.hardened = SparseTimeseriesStub()
        self.drained = SparseTimeseriesStub()
        self.undrained = SparseTimeseriesStub()
        self.flow_off = SparseTimeseriesStub()
        self.indraft = SparseTimeseriesStub()
        self.sewer = SparseTimeseriesStub()

    def __dict__(self):
        """returns dictionary of BucketOutcome to the given one."""
        return {'total': self.totals,
        'total_incoming': self.total_incoming,
        'total_outgoing': self.total_outgoing,
        'hardened': self.hardened,
        'drained': self.drained,
        'undrained': self.undrained,
        'flow_off': self.flow_off,
        'indraft': self.indraft,
        'sewer': self.sewer}

def event_tuple_values(events):
    """Return the list of event values from the given tuple of events."""
    return [event[1] for event in events]

def create_bucket_to_daily_outcome(buckets, daily_outcome):
    assert len(buckets) * 2 == len(daily_outcome)
    index = 0
    bucket2daily_outcome = {}
    for bucket in buckets:
        bucket2daily_outcome[bucket] = [daily_outcome[index * 2], daily_outcome[index * 2 + 1]]
        index = index + 1
    return bucket2daily_outcome

def total_daily_bucket_outcome(bucket2outcome):
    """Return the total daily flow off and net drainage of all buckets

    Parameters:
    * bucket2outcome -- dictionary of Bucket to BucketOutcome

    """
    generator = ()
    if len(bucket2outcome.keys()) > 0:
        buckets, outcomes = zip(*((b, o) for (b, o) in bucket2outcome.items()))
        interesting_timeseries = []
        for outcome in outcomes:
            interesting_timeseries.append(outcome.flow_off)
            interesting_timeseries.append(outcome.net_drainage)
        generator = ((event_tuple[0][0], create_bucket_to_daily_outcome(buckets, event_tuple_values(event_tuple))) \
                     for event_tuple in enumerate_events(*interesting_timeseries))
    return generator


class BucketSummarizer:
    """Computes the SingleDayBucketsSummary.

    Instance variables:
    * bucket2daily_outcome -- dictionary of Bucket to BucketOutcome
    """
    def __init__(self, bucket2daily_outcome={}):
        """Set the dictionary of Bucket to BucketOutcome to the given one."""
        self.bucket2daily_outcome = bucket2daily_outcome

    def compute(self):
        """Compute and return the SingleDayBucketsSummary."""
        summary = {}

        # Note that the time series computed for each bucket are computed from
        # the point of view the bucket:
        #   - a positive total means water flows to the buckets from the open
        #     water
        #   - a negative value means water flows from the buckets to the open
        #     water
        # So to get the volume that flows from the buckets to the open water we
        # have to negate the bucket total.

        summary['hardened'] = -self.compute_sum_hardened()
        summary['drained'] = -self.compute_sum_drained()
        summary['undrained'] = -self.compute_sum_undrained_net_drainage()
        summary['flow_off'] = -self.compute_sum_undrained_flow_off()
        summary['indraft'] = -self.compute_sum_indraft()
        summary['sewer'] = -self.compute_sum_sewer()
        summary['total_outgoing'] = summary['hardened'] + \
                         summary['drained'] + \
                         summary['undrained'] + \
                         summary['flow_off'] + \
                         summary['sewer']
        summary['total_incoming'] = summary['indraft']
        summary['total'] = summary['total_outgoing'] + summary['total_incoming']

        return summary

    def compute_sum_hardened(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == BucketTypes.HARDENED_SURFACE:
                sum += outcome[0]
        return sum

    def compute_sum_drained(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == BucketTypes.DRAINED_SURFACE:
                sum += outcome[0]
                net_drainage = outcome[1]
                if net_drainage < 0:
                    sum += net_drainage
        return sum

    def compute_sum_sewer(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == BucketTypes.STEDELIJK_SURFACE:
                net_drainage = outcome[1]
                # Unfortunately, net_drainage specifies flow off, which should
                # always be negative from the viewpoint of the bucket. For that
                # reason, we only take the negative values
                if net_drainage < 0:
                    sum += net_drainage
        return sum

    def compute_sum_undrained_net_drainage(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == BucketTypes.HARDENED_SURFACE or \
               bucket.surface_type == BucketTypes.UNDRAINED_SURFACE:
                net_drainage = outcome[1]
                if net_drainage < 0:
                    sum += net_drainage
        return sum

    def compute_sum_undrained_flow_off(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == BucketTypes.UNDRAINED_SURFACE:
                sum += outcome[0]
        return sum

    def compute_sum_indraft(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == BucketTypes.UNDRAINED_SURFACE or \
               bucket.surface_type == BucketTypes.HARDENED_SURFACE or \
               bucket.surface_type == BucketTypes.DRAINED_SURFACE:
                net_drainage = outcome[1]
                if net_drainage > 0:
                    sum += net_drainage
        return sum


class BucketsSummarizer:
    """Computes the BucketSummary from the outcome of each bucket."""
    def compute(self, bucket2outcome, start_date, end_date):
        """Returns the BucketsSummary of the given buckets.

        Parameters:
        * bucket2outcome --dictionary of Bucket to BucketOutcome

        """
        buckets_summary = BucketsSummary()
        for date, bucket2daily_outcome in total_daily_bucket_outcome(bucket2outcome):
            if date < start_date:
                continue
            if date >= end_date:
                break

            daily_summary = BucketSummarizer(bucket2daily_outcome).compute()
            buckets_summary.totals.add_value(date, daily_summary['total'])
            buckets_summary.total_outgoing.add_value(date, daily_summary['total_outgoing'])
            buckets_summary.total_incoming.add_value(date, daily_summary['total_incoming'])
            buckets_summary.hardened.add_value(date, daily_summary['hardened'])
            buckets_summary.drained.add_value(date, daily_summary['drained'])
            buckets_summary.undrained.add_value(date, daily_summary['undrained'])
            buckets_summary.flow_off.add_value(date, daily_summary['flow_off'])
            buckets_summary.indraft.add_value(date, daily_summary['indraft'])
            buckets_summary.sewer.add_value(date, daily_summary['sewer'])
        return buckets_summary
