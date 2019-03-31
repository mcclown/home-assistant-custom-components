import logging
import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt
from . import DATA_INDEX, ATTR_LAST_UPDATE, SCAN_INTERVAL

DEPENDENCIES = ['aquaillumination']
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination switch platform."""

    if DATA_INDEX not in hass.data:
        return False

    all_devices = []

    for host, device in hass.data[DATA_INDEX].items():

        if not device.connected:
            raise PlatformNotReady

        all_devices.append(AIAutomatedScheduleSwitch(device))

    add_devices(all_devices)


class AIAutomatedScheduleSwitch(SwitchDevice):
    """Representation of AI light schedule switch"""

    def __init__(self, device):
        """Initialise the AI switch"""
        self._device = device
        self._name = self._device.name + ' scheduled mode'
        self._state = None
    
    @property
    def name(self):
        """Get device name"""

        return self._name
    
    @property
    def should_poll(self):
        """Polling required"""

        return True

    @property
    def is_on(self):
        """return true if scheduled mode is enabled"""

        return self._state 

    @property
    def state(self):
        """Get device state"""
        
        if self._state:
            return "on"
        
        return "off"
    
    @property
    def device_state_attributes(self):

        return self._device.attr

    @property
    def available(self):
        """Return if the device is available"""

        if ATTR_LAST_UPDATE not in self.device_state_attributes:
            return False

        last_update = self.device_state_attributes[ATTR_LAST_UPDATE]

        return (dt.utcnow() - last_update) < (3 * self._device.throttle)

    def turn_on(self, **kwargs):
        """Enable schedule mode"""
        
        self._device.raw_device.set_schedule_state(True)

    def turn_off(self):
        """Disable schedule mode"""
        
        self._device.raw_device.set_schedule_state(False)

    async def async_update(self):
        """Fetch new state data for scheduled mode"""

        await self._device.async_update()
        self._state = self._device.schedule_state
