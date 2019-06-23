# Home-Assistant Custom Components

A proving ground for new compontents that I'm working on. The intention is to contribute them back to [Home Assistant](https://github.com/home-assistant/home-assistant) once they have been refined/tested.

##### Component Overview
* [AquaIllumination Lights](#aquaillumination-lights)
* [Seneye Water Sensors](#seneye-water-sensors)
* [uHoo Air Quality Monitor](#uhoo-air-quality-monitor)




### AquaIllumination Lights

Support for a range of aquarium lights, from AquaIllumination.

Based on top of one of a python modules I wrote, [AquaIPy](https://github.com/mcclown/AquaIPy). There is no documented API for AquaIllumination lights, so this has all had to be reverse engineered. Beta quality component, but still its use is at your own risk.

A brief rundown of features/caveats:

* This component implements 3 different types of platforms, for each light. A schedule enabled switch, a light for each channel and a sensor for each channel.
* Each individual light channel appears as a different light entity.
* Each individual light channel also has a corresponding sensor entity, with the brightness level. This is useful for graphing the light channel levels.
* It is possible to turn off the "scheduled mode" for the light but if it isn't turned off, then light brightness changes will appear for a few seconds then change back to the normal schedule.
* Support is only for the HD range of lights. No support for earlier models yet.
* No support for setting more than one channel at once.
* No support for increasing the channels to over 100% (the HD range). Although a schedule can still set values over 100%.

A sample configuration is shown below. This adds a light entity for each of the colour channels called <name>_<channel name>.

```YAML
aquaillumination:
  - host: 192.168.1.100
    name: sump ai
  - host: 192.168.1.101
    name: dt ai
```

I've been using this component with [this](https://github.com/thomasloven/lovelace-slider-entity-row) custom lovelace entity, which works pretty well. A sample lovelace configuration for this component is below, showing how multiple light entities are created.

```YAML

entities:
  - entity: light.sump_ai_uv
    step: 1
    type: 'custom:slider-entity-row'
  - entity: light.sump_ai_violet
    step: 1
    type: 'custom:slider-entity-row'
  - entity: light.sump_ai_royal
    step: 1
    type: 'custom:slider-entity-row'
  - entity: light.sump_ai_blue
    step: 1
    type: 'custom:slider-entity-row'
  - entity: light.sump_ai_green
    step: 1
    type: 'custom:slider-entity-row'
  - entity: light.sump_ai_deep_red
    step: 1
    type: 'custom:slider-entity-row'
  - entity: light.sump_ai_cool_white
    step: 1
    type: 'custom:slider-entity-row'
title: Sump Prime HD
type: entities
```

### Seneye Water Sensors

A digital sensor and monitoring system for aquariums and ponds.

Alpha quality component but low risk, as it's pretty simple. With some testing it should be beta quality shortly. Built on top of another module of mine, [pyseneye](https://github.com/mcclown/pyseneye).

* Support for these devices by plugging them in directly to the device that is running Home-Assistant. No need for a machine running the Seneye Connect App, or the Seneye Web Server.
* Support for pH, NH3 and temperature readings, support will be added for light reading shortly for Seneye Reef devices.
* No support for any Seneye API driven functions yet.
* No support for re-newing new slides, the Seneye device will need to be plugged into a PC running Seneye Connect or a Seneye Web Server, when a slide needs to be activated (once every 30 days).
* No data is synced to the cloud, so cloud alerts won't work either. You will need to setup appropriate alerting in Home-Assistant.

Configuration couldn't be simpler.

```YAML
sensor:
  - platform: seneye
```

### uHoo Air Quality Monitor

A air quality monitoring appliance, which syncs data to the cloud.

This API seems to only be available for enterprise customers currently but speak to uHoo if you have questions about that. Alpha quality but again, low risk, as it's only pulling data...should move towards beta quality quickly. Built on top of [pyuhooair](https://github.com/netmanchris/pyuhooair).

* Support for CO, CO<sub>2</sub>, NO<sub>2</sub>, O<sub>3</sub>, TVOC, Dust(PM2.5), Humidity and Air Pressure.
* No support for Temperature yet, as there is a bug in the underlying python module.
* Only updates from the API every 15 mins, data is cached by the pyuhooair implementation.

Configuration just needs email address and password:

```YAML
sensor:
  - platform: uhooair
    email: user@email.com
    password: SuperSecret12345
```
