# Home Assistant homee integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]
![][usage]

_Component to integrate with [homee][homee]._

Based on the intial work of [FreshlyBrewedCode]

Integration is in HACS Default Repositories now!

**This component will set up the following platforms.**

| Platform              | Description                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `alarm-control-panel` | Integrate the homee status.                                                                                                          |
| `binary_sensor`       | Integrate homee devices that provide binary state information like `on`/`off` or `open`/`close`.                                     |
| `climate`             | Integrate homee devices that provide temperature and can set a target temperature. Currently only heating thermostats are supported. |
| `cover`               | Integrate homee devices that provide motor and position functions such as blinds and shutter actuators                               |
| `event`               | Integrate events from button remots from homee.                                                                                      |
| `light`               | Integrate lights from homee.                                                                                                         |
| `lock`                | Integrate locks from homee.                                                                                                          |
| `number`              | Integrate number entities - usually settings of some kind.                                                                           |
| `sensor`              | Integrate homee devices that provide readings.                                                                                       |
| `switch`              | Integrate homee devices that can be turned `on`/`off` and can optionally provide information about the current power consumption.    |

![homee][homee_logo]

## Configuration

> :information_source: Because of a bug (#5) configuring **more than one** homee in Home Assistant can cause strange behavour - feedback is appreciated.

The integration will attempt to discover homee cubes in your network. Discovered cubes should show up in the "Configuration" -> "Integrations" section along with the associated homee id and host ip address.

1. In the HA UI go to "Configuration" -> "Integrations", click "Configure" on a discovered homee or click "+", search for "homee", and select the "homee" integration from the list.
   Or click here: [![Start Config Flow](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=homee)
2. In the dialog enter the username and password of a homee account that can access your cube, as well as the host (ip address of the homee cube) if you are not configuring a discovered cube.
   As well choose if you want to import all devices into HA or only ones from certain hommee-groups
   Click submit.
3. If the connection was successful you will see the "Group Configuration" section. if you chose "only devices from groups" in the first step, you can select the groups from which you want to import devices here.
   These options for door/window sensors can also be changed later from by clicking on the "Options" button on the homee integration. For more details on the available options check the [Options section](#Options).
4. Click submit. Your devices will be automatically added to Home Assistant.

## Options

The following table shows the available options that can be configured in the "Initial Configuration" step or using the "Options" button on an existing configuration. Please note that you have to restart Home Assistant after changing the options using the "Options" button.

| Option                                                                       | Default    | Description                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `The groups that should be imported`                                         | all groups | The integration will only import devices that are in any of the selected groups if you chose so in the first config step. Use this option to limit the devices that you want to import.                                                                                                                    |
| `Groups that contain window sensors`                                         | empty      | Any `binary_sensor` that is in any of the selected groups will use the `window` device class. You should select a homee group that contains all of your window sensors.                                                                                                                                    |
| `Groups that contain door sensors`                                           | empty      | Any `binary_sensor` that is in any of the selected groups will use the `door` device class. You should select a homee group that contains all of your door sensors.                                                                                                                                        |
| `Add (debug) information about the homee node and attributes to each entity` | `False`    | Enabling this option will add the `homee_data` attribute to every entity created by this integration. The attribute contains information about the homee node (name, id, profile) and the attributes (id, type). This option can be useful for debugging or advanced automations when used with templates. |

## Homee device not working correctly?

As of now this integration has support for very few devices. If you have Homee devices, that are not discovered or not working correctly, open an issue and do the following to provide a log:

1. Add following lines to configuration.yaml to enable info logging for hacs-homee:

```
logger:
  default: warn
  logs:
    custom_components.homee: info
```

2. Restart Home Assistant.
3. Go to "Settings->System->Logs" and show complete logs.
4. Look for lines containing "INFO (MainThread) \[homee]" and copy them
5. Open an issue describing the device and paste the logs in the corresponding section

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

Home Assistant encourages developers of integrations to use a separate python package that handles the communication between Home Assistant and the different devices (i.e. python api/backend). This integration uses [pymee](https://github.com/FreshlyBrewedCode/pymee) to connect and communicate with the homee websocket api. For some features it may be necessary to make changes to pymee first.

---

[homee]: https://hom.ee
[buymecoffee]: https://ko-fi.com/taraman
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/last-commit/Taraman17/hass-homee.svg?style=for-the-badge
[commits]: https://github.com/Taraman17/hass-homee/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Default-green.svg?style=for-the-badge
[homee_logo]: https://raw.githubusercontent.com/Taraman17/brands/master/custom_integrations/homee/logo.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/custom-components/blueprint.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Taraman17-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/Taraman17/hass-homee.svg?style=for-the-badge
[releases]: https://github.com/Taraman17/hass-homee/releases
[FreshlyBrewedCode]: https://github.com/FreshlyBrewedCode
[usage]: https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.homee.total
