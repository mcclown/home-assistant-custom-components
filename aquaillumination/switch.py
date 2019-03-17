import logging
import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv
from . import DATA_INDEX

DEPENDENCIES = ['aquaillumination']
_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination switch platform."""

    if DATA_INDEX not in hass.data:
        return False

    device = hass.data[DATA_INDEX]

    add_devices([AIAutomatedScheduleSwitch(device)])


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

    def turn_on(self, **kwargs):
        """Enable schedule mode"""
        
        self._device.set_schedule_state(True)

    def turn_off(self):
        """Disable schedule mode"""
        
        self._device.set_schedule_state(False)

    def update(self):
        """Fetch new state data for scheduled mode"""
        
        self._state = self._device.get_schedule_state()

