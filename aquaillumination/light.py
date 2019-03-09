import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import ( ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS, Light, PLATFORM_SCHEMA, LIGHT_TURN_ON_SCHEMA,
    VALID_BRIGHTNESS)
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['https://github.com/mcclown/AquaIPy/archive/1.0.1.zip#aquaipy==1.0.1']

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination platform."""

    from aquaipy import AquaIPy
    from aquaipy.error import FirmwareError, ConnError, MustBeParentError

    host = config.get(CONF_HOST)
    # If name isn't specified this fails to load. Need to fix this.
    name = config.get(CONF_NAME)

    # Setup connection with devices
    light = AquaIPy(name)

    try:
        light.connect(host)
    except FirmwareError:
        _LOGGER.error("Invalid firmware version for target device")
        return
    except ConnError:
        _LOGGER.error("Unable to connect to specified device, please verify the host name")
        return
    except MustBeParentError:
        _LOGGER.error("The specifed device must be the parent light, if paired. Please verify")

    colors = light.get_colors()

    add_devices(AquaIllumination(light, color, name) for color in colors)


class AquaIllumination(Light):
    """Representation of an AquaIllumination light"""

    def __init__(self, light, channel, parent_name):
        """Initialise the AquaIllumination light"""
        self._light = light
        self._name = parent_name + ' ' + channel
        self._state = None
        self._brightness = None
        self._channel = channel
    
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
        """return true if light is on"""

        return self._state == 'on' or self._state == 'schedule_mode' 

    @property
    def state(self):
        """Get device state"""

        return self._state

    @property
    def supported_features(self):
        """Flag supported features"""
        
        return SUPPORT_BRIGHTNESS

    @property
    def brightness(self):
        """Return brightness level"""

        return self._brightness


    def turn_on(self, **kwargs):
        """Turn all color channels to given percentage"""

        brightness = (kwargs.get(ATTR_BRIGHTNESS, 255) / 255) * 100
        colors_pct = self._light.get_colors_brightness()

        for color,val in colors_pct.items():
            
            # For the moment we don't support HD mode, for these lights. This
            # means that we limit all channels to a max of 100%, when setting
            # the brightness. The next part works around that, until this 
            # support is added.
            
            if val > 100:
                color_pct[color] = 100

        colors_pct[self._channel] = brightness

        _LOGGER.debug("Turn on result: " + str(colors_pct))
        self._light.set_colors_brightness(colors_pct)


    def turn_off(self):
        """Turn all color channels to 0%"""

        colors_pct = self._light.get_colors_brightness()
        colors_pct[self._channel] = 0

        self._light.set_colors_brightness(colors_pct)

    
    def update(self):
        """Fetch new state data for this light"""
        
        sched_state = self._light.get_schedule_state()
        colors_pct = self._light.get_colors_brightness()
        brightness = colors_pct[self._channel]
        
        self._state = "off"

        if sched_state:
            self._state = 'schedule_mode'
        elif brightness > 0:
            self._state = 'on'

        self._brightness = (brightness / 100) * 255


