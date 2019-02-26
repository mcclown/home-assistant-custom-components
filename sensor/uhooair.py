"""
Support for the uHoo indoor air quality monitor.

For more details about this platform, please refer to the documentation at
https://github.com/mcclown/home-assistant-custom-components
"""

from datetime import timedelta, datetime
import logging
import math

import voluptuous as vol

from homeassistant.const import (
    CONF_EMAIL, CONF_PASSWORD, CONF_DEVICES, DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle, dt

REQUIREMENTS = ['pyuhooair==0.0.1']

_LOGGER = logging.getLogger(__name__)

ATTR_SCORE = 'score'
ATTR_TIMESTAMP = 'timestamp'
ATTR_LAST_API_UPDATE = 'last_api_update'
ATTR_COMPONENT = 'component'
ATTR_VALUE = 'value'
ATTR_SENSORS = 'sensors'

DEVICE_CLASS_PM2_5 = 'PM2.5'
DEVICE_CLASS_CARBON_DIOXIDE = 'Carbon Dioxide'
DEVICE_CLASS_CARBON_MONOXIDE = 'Carbon Monoxide'
DEVICE_CLASS_VOLATILE_ORGANIC_COMPOUNDS = 'TVOC'
DEVICE_CLASS_OZONE = 'Ozone'
DEVICE_CLASS_NITROGEN_DIOXIDE = 'Nitrogen Dioxide'
DEVICE_CLASS_AIR_PRESSURE = 'Air Pressure'

SENSOR_TYPES = {
    #'TEMP': {'device_class': DEVICE_CLASS_TEMPERATURE, - Bug in underlying library, not available.
    #         'unit_of_measurement': TEMP_CELSIUS,
    #         'icon': 'mdi:thermometer'},
    'humidity': {'device_class': DEVICE_CLASS_HUMIDITY,
              'unit_of_measurement': '%',
              'icon': 'mdi:water-percent'},
    'co2': {'device_class': DEVICE_CLASS_CARBON_DIOXIDE,
            'unit_of_measurement': 'ppm',
            'icon': 'mdi:periodic-table-co2'},
    'CO': {'device_class': DEVICE_CLASS_CARBON_MONOXIDE,
            'unit_of_measurement': 'ppm',
            'icon': 'mdi:cloud'},
    'voc': {'device_class': DEVICE_CLASS_VOLATILE_ORGANIC_COMPOUNDS,
            'unit_of_measurement': 'ppb',
            'icon': 'mdi:cloud'},
    'dust': {'device_class': DEVICE_CLASS_PM2_5,
             'unit_of_measurement': 'µg/m3',
             'icon': 'mdi:cloud'},
    'ozone': {'device_class': DEVICE_CLASS_OZONE,
             'unit_of_measurement': 'ppb',
             'icon': 'mdi:cloud'},
    'NO2': {'device_class': DEVICE_CLASS_NITROGEN_DIOXIDE,
             'unit_of_measurement': 'ppb',
             'icon': 'mdi:cloud'},
    'air_pressure': {'device_class': DEVICE_CLASS_AIR_PRESSURE,
              'unit_of_measurement': 'nPa',
              'icon': 'mdi:cloud'},
}

# This is the minimum time between throttled update calls.
# Don't bother asking us for state more often than that.
SCAN_INTERVAL = timedelta(minutes=5)

#UHOOAIR_DEVICE_SCHEMA = vol.Schema({
#    vol.Required(CONF_SERIAL_NUMBER): cv.string,
#})

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
    #vol.Optional(CONF_DEVICES): vol.All(cv.ensure_list, [UHOOAIR_DEVICE_SCHEMA]),
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Connect to the uHoo API and find devices."""
    from pyuhooair.auth import UhooAuth
    from pyuhooair.data import get_all_devices
    from pyuhooair.objects import UhooDev

    auth = UhooAuth(config[CONF_EMAIL], config[CONF_PASSWORD])

    try:
        all_devices = []
        devices = get_all_devices(auth)

        for device in devices:

            name = device["deviceName"]
            _LOGGER.debug("Found uHoo device: %s", name)

            # UhooDev class automatically throttles reads to once every 15 min
            # and caches results in the object. No need for additional
            # caching data class.
            uhoo_data = UhooDev(name, auth)
            
            for sensor in SENSOR_TYPES:
                if sensor in uhoo_data._data:
                    uhoo_sensor = UhooAirSensor(uhoo_data, device, sensor)
                    all_devices.append(uhoo_sensor)

        async_add_entities(all_devices, True)
        return
    except Exception as e:
        _LOGGER.error("Error: {0}".format(e))

    raise PlatformNotReady


class UhooAirSensor(Entity):
    """Implementation of a uHooAir device."""

    def __init__(self, data, device, sensor_type):
        """Initialize the sensor."""
        self._uuid = device["serialNumber"]
        self._device_class = SENSOR_TYPES[sensor_type]['device_class']
        self._name = '{0} {1}'.format(device['deviceName'], self._device_class)
        unit = SENSOR_TYPES[sensor_type]['unit_of_measurement']
        self._unit_of_measurement = unit
        self._data = data
        self._type = sensor_type

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return SENSOR_TYPES[self._type]['icon']

    @property
    def state(self):
        """Return the state of the device."""
        return self._data.get_state(self._type)

    @property
    def device_state_attributes(self):
        """Return additional attributes."""
        return {}

    @property
    def available(self):
        """Device availability based on the last update timestamp."""

        last_api_read = self._data.get_state("DateTime")

        p_time = dt.parse_datetime(last_api_read)

        #p_time = datetime.strptime(last_api_read, "%Y-%m-%d %H:%M")

        return (dt.utcnow() - dt.as_utc(p_time)) < (timedelta(minutes=60))

    @property
    def unique_id(self):
        """Return the unique id of this entity."""
        return "{}_{}".format(self._uuid, self._type)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """Should device be polled"""
        return True

