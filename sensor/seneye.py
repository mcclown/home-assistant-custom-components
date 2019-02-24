"""
Support for the Seneye range of aquarium and pond sensors.
For more details about this platform, please refer to the documentation at
https://github.com/mcclown/home-assistant-custom-components
"""

from datetime import timedelta
import logging

from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle, dt

REQUIREMENTS = ['https://github.com/mcclown/pyseneye/archive/0.0.1.zip#pyseneye==0.0.1']

_LOGGER = logging.getLogger(__name__)

ATTR_TIMESTAMP = 'timestamp'
ATTR_LAST_SLIDE_READ = 'last_slide_update'

DEVICE_CLASS_PH = 'PH'
DEVICE_CLASS_FREE_AMMONIA = 'NH3'

UNIT_POWER_OF_HYDROGEN = 'pH'
UNIT_PARTS_PER_MILLION = 'ppm'

SENSOR_TYPES = {
    'temperature': {'device_class': DEVICE_CLASS_TEMPERATURE,
             'unit_of_measurement': TEMP_CELSIUS,
             'icon': 'mdi:thermometer'},
    'ph': {'device_class': DEVICE_CLASS_PH,
              'unit_of_measurement': UNIT_POWER_OF_HYDROGEN,
              'icon': 'mdi:alpha-h-box-outline'},
    'nh3': {'device_class': DEVICE_CLASS_FREE_AMMONIA,
            'unit_of_measurement': UNIT_PARTS_PER_MILLION,
            'icon': 'mdi:alpha-n-box-outline'}
}

SCAN_INTERVAL = timedelta(minutes=5)
SENEYE_SLIDE_READ_INTERVAL = timedelta(minutes=30)

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Connect to the Seneye device."""
    from pyseneye.sud import SUDevice, Action, DeviceType

    try:

        device = SUDevice()
        data = device.action(Action.ENTER_INTERACTIVE_MODE)
        device_type = data.device_type

        seneye_data = SeneyeData(device, SENEYE_SLIDE_READ_INTERVAL)
        
        await seneye_data.async_update()
        
        all_sensors = []

        for sensor in SENSOR_TYPES:
            if sensor in seneye_data.data:
                seneye_sensor = SeneyeSensor(seneye_data, sensor, SENEYE_SLIDE_READ_INTERVAL)
                all_sensors.append(seneye_sensor)

        async_add_entities(all_sensors, True)

        return

    except Exception as e:
        _LOGGER.error("Error: {0}".format(e))

    raise PlatformNotReady


class SeneyeSensor(Entity):
    """Implementation of a Seneye sensor."""

    def __init__(self, data, sensor_type, throttle):
        """Initialize the sensor."""
        self._device_class = SENSOR_TYPES[sensor_type]['device_class']
        self._name = 'Seneye {}'.format(self._device_class)
        unit = SENSOR_TYPES[sensor_type]['unit_of_measurement']
        self._unit_of_measurement = unit
        self._data = data
        self._type = sensor_type
        self._throttle = throttle

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
        return self._data.data[self._type]

    @property
    def device_state_attributes(self):
        """Return additional attributes."""
        raw_dt = self._data.attrs[ATTR_LAST_SLIDE_READ]

        # Convert timestamp to local time, then format it.
        local_dt = dt.as_local(raw_dt)
        formatted_dt = local_dt.strftime("%Y-%m-%d %H:%M:%S")
       
        return { ATTR_LAST_SLIDE_READ: formatted_dt }

    @property
    def available(self):
        """Device availability based on the last update timestamp.
        
        Data should be updating every 30mins, so we'll say it's unavailable
        if it takes over an hour to update.
        """
        if ATTR_LAST_SLIDE_READ not in self._data.attrs:
            return False

        last_api_data = self._data.attrs[ATTR_LAST_SLIDE_READ]
        return (dt.utcnow() - last_api_data) < (2 * self._throttle)

    @property
    def unique_id(self):
        """Return the unique id of this entity."""
        return "seneye_{}".format(self._type)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return self._unit_of_measurement

    async def async_update(self):
        """Get the latest data."""
        await self._data.async_update()


class SeneyeData:
    """Get data from Seneye device."""

    def __init__(self, device, throttle):
        """Initialize the data object."""
        self._device = device
        self.data = {}
        self.attrs = {}
        self.async_update = Throttle(throttle)(self._async_update)

    async def _async_update(self):
        """Get the data from Awair API."""
        from pyseneye.sud import Action

        resp = self._device.action(Action.SENSOR_READING)

        if not resp:
            return

        self.attrs[ATTR_LAST_SLIDE_READ] = dt.utcnow()

        for sensor in SENSOR_TYPES:

            self.data[sensor] = getattr(resp, sensor, None)

        _LOGGER.debug("Got Seneye data")
