import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import ( ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS, Light, LIGHT_TURN_ON_SCHEMA,
    VALID_BRIGHTNESS)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt

from . import DATA_INDEX, ATTR_LAST_UPDATE, SCAN_INTERVAL

DEPENDENCIES = ['aquaillumination']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination light platform."""

    if DATA_INDEX not in hass.data:
        return False

    all_devices = []

    for host, device in hass.data[DATA_INDEX].items():

        if not device.connected:
            raise PlatformNotReady

        colors = device.raw_device.get_colors()

        for color in colors:
            all_devices.append(AquaIllumination(device, color))

    add_devices(all_devices)


class AquaIllumination(Light):
    """Representation of an AquaIllumination light"""

    def __init__(self, light, channel):
        """Initialise the AquaIllumination light"""
        self._light = light
        self._name = self._light.name + ' ' + channel.replace("_", " ")
        self._state = None
        self._brightness = None
        self._channel = channel
        self._unique_id = "{0}-{1}".format(self._light.mac_addr, self._channel)
    
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

    @property
    def device_state_attributes(self):

        return self._light.attr

    @property
    def available(self):
        """Return if the device is available"""

        if ATTR_LAST_UPDATE not in self.device_state_attributes:
            return False

        last_update = self.device_state_attributes[ATTR_LAST_UPDATE]

        return (dt.utcnow() - last_update) < (3 * self._light.throttle)

    @property
    def unique_id(self):

        return self._unique_id

    def turn_on(self, **kwargs):
        """Turn color channel to given percentage"""

        brightness = (kwargs.get(ATTR_BRIGHTNESS, 255) / 255) * 100
        colors_pct = self._light.raw_device.get_colors_brightness()

        for color,val in colors_pct.items():
            
            # For the moment we don't support HD mode, for these lights. This
            # means that we limit all channels to a max of 100%, when setting
            # the brightness. The next part works around that, until this 
            # support is added.
            
            if val > 100:
                colors_pct[color] = 100

        colors_pct[self._channel] = brightness

        _LOGGER.debug("Turn on result: " + str(colors_pct))
        self._light.raw_device.set_colors_brightness(colors_pct)

    def turn_off(self):
        """Turn all color channels to 0%"""

        colors_pct = self._light.raw_device.get_colors_brightness()
        colors_pct[self._channel] = 0

        self._light.raw_device.set_colors_brightness(colors_pct)
    
    async def async_update(self):
        """Fetch new state data for this light"""
        
        await self._light.async_update()
        
        brightness = self._light.colors_brightness[self._channel]
        self._state = "off"

        if brightness > 0:
            self._state = 'on'

        self._brightness = (brightness / 100) * 255
