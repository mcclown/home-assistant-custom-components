import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import ( ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS, Light, LIGHT_TURN_ON_SCHEMA,
    VALID_BRIGHTNESS)
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv
from . import DATA_INDEX

DEPENDENCIES = ['aquaillumination']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination light platform."""

    if DATA_INDEX not in hass.data:
        return False

    light = hass.data[DATA_INDEX]
    colors = light.get_colors()

    add_devices(AquaIllumination(light, color) for color in colors)


class AquaIllumination(Light):
    """Representation of an AquaIllumination light"""

    def __init__(self, light, channel):
        """Initialise the AquaIllumination light"""
        self._light = light
        self._name = self._light.name + ' ' + channel.replace("_", " ")
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
        """Turn color channel to given percentage"""

        brightness = (kwargs.get(ATTR_BRIGHTNESS, 255) / 255) * 100
        colors_pct = self._light.get_colors_brightness()

        for color,val in colors_pct.items():
            
            # For the moment we don't support HD mode, for these lights. This
            # means that we limit all channels to a max of 100%, when setting
            # the brightness. The next part works around that, until this 
            # support is added.
            
            if val > 100:
                colors_pct[color] = 100

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

        if brightness > 0:
            self._state = 'on'

        self._brightness = (brightness / 100) * 255


