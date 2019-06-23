import logging

from homeassistant.const import DEVICE_CLASS_ILLUMINANCE
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.util import dt
from . import DATA_INDEX, ATTR_LAST_UPDATE, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

UNIT_PERCENT = '%'

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the AquaIllumination light platform."""

    if DATA_INDEX not in hass.data:
        return False

    all_entities = []

    for host, device in hass.data[DATA_INDEX].items():

        if not device.connected:
            raise PlatformNotReady

        colors = await device.raw_device.async_get_colors()

        for color in colors:
            all_entities.append(AquaIlluminationChannelBrightness(device, color))

    add_entities(all_entities)


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
        self._unique_id = "{0}_{1}_sensor".format(self._device.mac_addr, channel) 
    
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
    
    @property
    def device_state_attributes(self):

        return self._device.attr

    @property
    def available(self):
        """Return if the device is available"""

        if ATTR_LAST_UPDATE not in self.device_state_attributes:
            return False

        last_update = self.device_state_attributes[ATTR_LAST_UPDATE]

        return (dt.utcnow() - last_update) < (2 * self._device.throttle)
    
    async def async_update(self):
        """Fetch new state data for this channel"""

        await self._device.async_update()
        
        brightness = self._device.colors_brightness[self._channel]
        self._state = float("{0:.2f}".format(brightness))
