import logging
import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['https://github.com/mcclown/AquaIPy/archive/1.0.2.zip#aquaipy==1.0.2']

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination platform."""

    from aquaipy import AquaIPy
    from aquaipy.error import FirmwareError, ConnError, MustBeParentError

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    # Setup connection with devices
    device = AquaIPy(name)

    try:
        device.connect(host)
    except FirmwareError:
        _LOGGER.error("Invalid firmware version for target device")
        return
    except ConnError:
        _LOGGER.error("Unable to connect to specified device, please verify the host name")
        return
    except MustBeParentError:
        _LOGGER.error("The specifed device must be the parent light, if paired. Please verify")

    add_devices([AIAutomatedScheduleSwitch(device, name)])


class AIAutomatedScheduleSwitch(SwitchDevice):
    """Representation of AI light schedule switch"""

    def __init__(self, device, parent_name):
        """Initialise the AI switch"""
        self._device = device
        self._name = parent_name + ' scheduled mode'
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

