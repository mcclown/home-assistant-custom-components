"""The AquaIllumination Light component"""
from datetime import timedelta
import logging
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle, dt


REQUIREMENTS = ['AquaIPy==2.0.1']
_LOGGER = logging.getLogger(__name__)

ATTR_LAST_UPDATE = 'last_update'
DOMAIN = 'aquaillumination'
DATA_INDEX = "data_" + DOMAIN

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(
        cv.ensure_list, [vol.Schema({
            vol.Required(CONF_HOST): cv.string,
            vol.Required(CONF_NAME): cv.string
        })]
    )
}, extra=vol.ALLOW_EXTRA)

DEVICE_TYPES = ['light', 'switch', 'sensor']
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup(hass, hass_config):
    """Setup the AquaIllumination component"""

    if DATA_INDEX not in hass.data:
        hass.data[DATA_INDEX] = {}

    for config in hass_config.get(DOMAIN, []):
        await _async_setup_ai_device(hass, hass_config, config)

    for device in DEVICE_TYPES:
        hass.async_create_task(discovery.async_load_platform(
            hass, device, DOMAIN, config, hass_config))

    return True


async def _async_setup_ai_device(hass, hass_config, config):
    """Setup an individual device"""

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    if host in hass.data[DATA_INDEX]:
        return

    # Setup connection with devices
    device = AIData(host, name, SCAN_INTERVAL)
    
    await device.async_update()
    hass.data[DATA_INDEX][host] = device


class AIData:
    """Class for handling data from AI devices and caching."""

    def __init__(self, host, name, throttle):

        from aquaipy import AquaIPy

        self.attr = {}
        self._connected = False
        self._device = AquaIPy(name)
        self._t = throttle
        self._colors_brightness = None
        self._schedule_state = None
        self._host = host

        self.async_update = Throttle(throttle)(self._async_update)

    @property
    def name(self):
        return self._device.name

    @property
    def mac_addr(self):
        return self._device.mac_addr
    
    @property
    def connected(self):

        return self._connected

    @property
    def colors_brightness(self):

        return self._colors_brightness

    @property
    def raw_device(self):

        return self._device

    @property
    def schedule_state(self):

        return self._schedule_state

    @property
    def throttle(self):

        return self._t

    async def _async_update(self):

        if not self.connected:
            from aquaipy.error import FirmwareError, ConnError, MustBeParentError
            
            try:
                await self._device.async_connect(self._host)
            except FirmwareError:
                _LOGGER.error("Invalid firmware version for target device")
                return
            except ConnError:
                _LOGGER.error("Unable to connect to specified device, please verify the host name")
                return
            except MustBeParentError:
                _LOGGER.error("The specifed device must be the parent light, if paired. Please verify")
                return

            self._connected = True
            
        self._colors_brightness = await self._device.async_get_colors_brightness()
        self._schedule_state = await self._device.async_get_schedule_state()

        self.attr[ATTR_LAST_UPDATE] = dt.utcnow()
