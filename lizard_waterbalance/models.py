# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# $Id$

from django.db import models
from django.utils.translation import ugettext as _

from lizard_fewsunblobbed.models import Timeserie
from lizard_map.models import ColorField


# Create your models here.


class WaterbalanceTimeserie(models.Model):
    """Connects time series to a WaterbalanceLabel.

    Instance variables:
    * label -- link to the WaterbalanceLabel that describes the time serie
    * volume -- link to the volume time serie data
    * chloride -- link to the chloride time serie data
    * phosphate -- link to the phosphate time serie data
    * nitrate -- link to the nitrate time serie data
    * sulfate -- link to the sulfate time serie data

    """
    label = models.ForeignKey('WaterbalanceLabel')
    volume = models.ForeignKey(Timeserie, related_name='+')
    chloride = models.ForeignKey(Timeserie, related_name='+')
    phosphate = models.ForeignKey(Timeserie, related_name='+')
    nitrate = models.ForeignKey(Timeserie, related_name='+')
    sulfate = models.ForeignKey(Timeserie, related_name='+')


class Bucket(models.Model):
    """Represents a *bakje*.

    Instance variables:
    * name -- name to show to the user
    * surface -- surface in [ha]
    * is_collapsed -- holds if and only if the bucket is a single bucket
    * open_water -- link to the open water
    * indraft -- link to input time serie for *intrek*
    * drainage -- link to input time serie for drainage
    * seepage -- link to input time serie for *kwel*
    * infiltration -- link to input time serie for *wegzijging*
    * flow_off -- link to input time serie for *afstroming*
    * computed_flow_off -- link to computed time serie for *afstroming*

    """
    name = models.CharField(verbose_name="naam", max_length=64)
    surface = models.IntegerField(verbose_name=_("oppervlakte"),
                                  help_text=_("oppervlakte in hectares"))

    # We couple a bucket to the open water although from a semantic point of
    # view, an open water should reference the buckets. However, this is the
    # usual way to implement a one-to-many relationship.
    open_water = \
        models.ForeignKey("Bucket", blank=True, related_name='buckets')

    indraft = models.ForeignKey(WaterbalanceTimeserie,
                                verbose_name=_("intrek"),
                                help_text=_("tijdserie naar intrek"),
                                related_name='+')
    drainage = models.ForeignKey(WaterbalanceTimeserie,
                                 verbose_name=_("drainage"),
                                 help_text=_("tijdserie naar drainage"),
                                 related_name='+')
    seepage = models.ForeignKey(WaterbalanceTimeserie,
                                verbose_name=_("kwel"),
                                help_text=_("tijdserie naar kwel"),
                                related_name='+')
    infiltration = models.ForeignKey(WaterbalanceTimeserie,
                                     verbose_name=_("wegzijging"),
                                     help_text=_("tijdserie naar wegzijging"),
                                     related_name='+')
    flow_off = models.ForeignKey(WaterbalanceTimeserie,
                                 verbose_name=_("afstroming"),
                                 help_text=_("tijdserie naar afstroming"),
                                 related_name='+')
    computed_flow_off = \
        models.ForeignKey(WaterbalanceTimeserie,
                          verbose_name=_("berekende afstroming"),
                          help_text=_("tijdserie naar berekende afstroming"),
                          related_name='+')

    # We may need to add time series to store the inputs in the the right
    # units. For example, chances are seepage is specified in cubic milimeters
    # per hour. Internally however, we will probably use cubic meters and it
    # could be handy to store these values explicitly.


class OpenWater(Bucket):
    """Represents an *open water(bakje)*.

    Instance variables:
    * minimum_level -- link to time series for minimum water level in [m]
    * maximum_level -- link to time series for maximum water level in [m]
    * target_level -- link to time series for target water level in [m]
    * sluice_error -- link to computed time series for model errors

    To get to the buckets that have access to the current open water, use the
    implicit attribute 'buckets' which is a Manager for these buckets.

    To get to the pumps of the current open water, use the implicit attribute
    'pumping_stations', which is a Manager for these pumps.

    """
    minimum_level = models.ForeignKey(WaterbalanceTimeserie,
        verbose_name=_("ondergrens"),
        help_text=_("tijdserie naar ondergrens peil in meters"),
        related_name='+')
    maximum_level = models.ForeignKey(WaterbalanceTimeserie,
        verbose_name=_("bovengrens"),
        help_text=_("tijdserie naar bovengrens peil in meters"),
        related_name='+')
    target_level = models.ForeignKey(WaterbalanceTimeserie,
        verbose_name=_("streefpeil"),
        help_text=_("tijdserie met streefpeil in meters"),
        related_name='+')
    sluice_error = models.ForeignKey(WaterbalanceTimeserie,
        verbose_name= _("sluitfout"),
        help_text=_("tijdserie met sluitfout"),
        related_name='+')


class PumpingStation(models.Model):
    """Represents a pump that pumps water into or out of the open water.

    Instance variables:
    * open_water -- link to the OpenWater
    * into -- holds if and only if the pump pumps water into the open water
    * percentage -- percentage of water through through this pump

    If this pump pumps water into (out of) the open water, the percentage is
    the percentage of incoming water that is pumped into (out of) the open
    water.

    """
    open_water = models.ForeignKey(OpenWater, related_name='pumping_stations')
    into = models.BooleanField()
    percentage = models.FloatField()


class PumpLine(models.Model):
    """Represents a *pomplijn*.

    Instance variables:
    * pump -- link to the pump to which this pumpline belongs
    * timeserie -- link to the time serie that contains the data

    """
    pump = models.ForeignKey(PumpingStation, related_name='pump_lines')
    timeserie = models.ForeignKey(WaterbalanceTimeserie, related_name='+')


class WaterbalanceArea(models.Model):
    """Represents the area of which we want to know the waterbalance.

    Instance variables:
    * name -- name to show to the user
    * slug -- unique name to construct the URL
    * description -- general description
    * precipitation -- link to time series for *neerslag*
    * evaporation -- link to time series for *verdamping*

    """
    class Meta:
        verbose_name = _("Waterbalans gebied")
        verbose_name_plural = _("Waterbalans gebieden")
        ordering = ("name",)

    name = models.CharField(max_length=80)
    slug = models.SlugField(help_text=_("Name to construct the URL."))
    description = models.TextField(null=True,
                                   blank=True,
                                   help_text="You can use markdown")

    precipitation = models.ForeignKey(WaterbalanceTimeserie,
                                      related_name='+',
                                      null=True,
                                      blank=True)
    evaporation = models.ForeignKey(WaterbalanceTimeserie,
                                    related_name='+',
                                    null=True,
                                    blank=True)
    open_water = models.ForeignKey(OpenWater, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('krw_waternet.waterbalance', (), {'area': str(self.slug)})


class WaterbalanceLabel(models.Model):
    """Specifies the labels of a water balance and their color.

    Instance variables:
    * name -- name of the group of parameters to which the parameter belongs
    * parent -- link to a possible parent label to specify a hierarchy
    * type -- incoming flow, outgoing flow or error flow
    * color -- hex code of the color that identifies the parameter group
    * order_index -- index to determine the order of the labels in a legend

    """

    class Meta:
        verbose_name = _("Waterbalans label")
        verbose_name_plural = _("Waterbalans labels")
        ordering = ("order_index",)

    TYPE_IN = 1
    TYPE_OUT = 2
    TYPE_ERROR = 3

    TYPES = ((TYPE_IN, 'in'), (TYPE_OUT, 'out'), (TYPE_ERROR, 'fout'))

    name = models.CharField(max_length=64)
    parent = models.ForeignKey('WaterbalanceLabel', null=True, blank=True)
    flow_type = models.IntegerField(choices=TYPES, default=TYPE_IN)
    color = ColorField()
    order_index = models.IntegerField(unique=True)

    def __unicode__(self):
        return self.name
