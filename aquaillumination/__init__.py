"""The AquaIllumination Light component"""
import logging
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv


REQUIREMENTS = ['AquaIPy==1.0.2']

LOGGER = logging.getLogger(__name__)

DOMAIN = 'aquaillumination'
DATA_INDEX = "data_" + DOMAIN

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_NAME): cv.string
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, hass_config):
    """Setup the AquaIllumination light component"""

    from aquaipy import AquaIPy
    from aquaipy.error import FirmwareError, ConnError, MustBeParentError

    config = hass_config.get(DOMAIN, [])

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    # Setup connection with devices
    device = AquaIPy(name)

    try:
        device.connect(host)
    except FirmwareError:
        _LOGGER.error("Invalid firmware version for target device")
        return False
    except ConnError:
        _LOGGER.error("Unable to connect to specified device, please verify the host name")
        return False
    except MustBeParentError:
        _LOGGER.error("The specifed device must be the parent light, if paired. Please verify")
        return False

    hass.data[DATA_INDEX] = device

    hass.async_create_task(discovery.async_load_platform(
        hass, 'light', DOMAIN, config, hass_config))

    hass.async_create_task(discovery.async_load_platform(
        hass, 'switch', DOMAIN, config, hass_config))

    return True




