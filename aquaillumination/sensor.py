import logging

from homeassistant.const import DEVICE_CLASS_ILLUMINANCE 
from homeassistant.helpers.entity import Entity
from . import DATA_INDEX

DEPENDENCIES = ['aquaillumination']

_LOGGER = logging.getLogger(__name__)

UNIT_PERCENT = '%'

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the AquaIllumination light platform."""

    if DATA_INDEX not in hass.data:
        return False

    for host, device in hass.data[DATA_INDEX].items():
        colors = device.get_colors()

        add_entities(AquaIlluminationChannelBrightness(device, color) for color in colors)


class AquaIlluminationChannelBrightness(Entity):
    """Representation of an AquaIllumination light brightness"""

    def __init__(self, device, channel):
        """Initialise the AquaIllumination channel"""
        self._device = device
        self._name = '{0} {1} brightness'.format(
                self._device.name,
                channel.replace('_', ' '))
        self._state = None
        self._channel = channel
        self._unique_id = "{0}_{1}".format(self._device.mac_addr, channel) 
    
    @property
    def name(self):
        """Get device name"""

        return self._name
    
    @property
    def should_poll(self):
        """Polling required"""

        return True

    @property
    def state(self):
        """Get device state"""

        return self._state
    
    @property
    def device_class(self):
        return DEVICE_CLASS_ILLUMINANCE

    @property
    def icon(self):
        return "mdi:brightness-percent"

    @property
    def unit_of_measurement(self):

        return UNIT_PERCENT

    @property
    def unique_id(self):

        return self._unique_id
    
    def update(self):
        """Fetch new state data for this channel"""
        
        colors_pct = self._device.get_colors_brightness()
        brightness = colors_pct[self._channel]
        
        self._state = float("{0:.2f}".format(brightness))


