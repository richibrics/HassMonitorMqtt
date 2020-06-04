
import logging
import re
import sys
from subprocess import check_output, CalledProcessError

from copy import deepcopy

import voluptuous as vol

import homeassistant.loader as loader
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
import homeassistant.util.dt as dt_util
import homeassistant.helpers.config_validation as cv
from homeassistant.components import recorder
from homeassistant.components.sensor import (DOMAIN, PLATFORM_SCHEMA)
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from homeassistant.components.mqtt import (
    ATTR_DISCOVERY_HASH,
    CONF_QOS,
    CONF_UNIQUE_ID,
    MqttAttributes,
    MqttAvailability,
    MqttDiscoveryUpdate,
    MqttEntityDeviceInfo,
    subscription,
)

DEPENDENCIES = ["mqtt"]

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "monitor_mqtt"

CONF_CLIENT_NAME = "client_name"

MONITOR_MQTT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_NAME): cv.string,
    }
)


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [MONITOR_MQTT_SCHEMA]))}, extra=vol.ALLOW_EXTRA
)


inbox_information = [{'id': 'ram', 'name': 'ram_used_percentage', 'sensor_label': 'Ram used percentage', 'unity': '%', 'icon': 'mdi:memory', 'device_class': None, 'value': None},
                     {'id': 'cpu', 'name': 'cpu_used_percentage',
                      'sensor_label': 'CPU used percentage', 'unity': '%', 'icon': 'mdi:calculator-variant', 'device_class': None, 'value': None},
                     {'id': 'disk', 'name': 'disk_used_percentage',
                      'sensor_label': 'Disk used percentage', 'unity': '%', 'icon': 'mdi:harddisk', 'device_class': None, 'value': None},
                     {'id': 'os', 'name': 'operating_system',
                      'sensor_label': 'Operating system', 'unity': '', 'icon': 'mdi:$OPERATING_SYSTEM', 'device_class': None, 'value': None},
                     {'id': 'battery_level', 'name': 'battery_level_percentage',
                      'sensor_label': 'Battery percentage', 'unity': '%', 'icon': 'mdi:battery', 'device_class': 'battery', 'value': None},
                     {'id': 'battery_charging', 'name': 'battery_charging',
                      'sensor_label': 'Battery charging', 'unity': '', 'icon': 'mdi:$PLUGGED', 'device_class': None, 'value': None},
                     {'id': 'cpu_temperature', 'name': 'cpu_temperature',
                      'sensor_label': 'CPU temperature', 'unity': '°C', 'icon': 'mdi:coolant-temperature', 'device_class': 'temperature', 'value': None},
                     {'id': 'time', 'name': 'message_time', 'sensor_label': 'Last update time', 'unity': '', 'icon': 'mdi:clock-outline', 'device_class': None, 'value': None}]


outbox_information = [{'id': 'shutdown', 'name': 'shutdown_command', 'sensor_label': 'Shutdown', 'icon': 'mdi:power'},
                      {'id': 'reboot', 'name': 'reboot_command',
                       'sensor_label': 'Reboot', 'icon': 'mdi:restart'},
                      {'id': 'lock', 'name': 'lock_command',
                       'sensor_label': 'Lock', 'icon': 'mdi:lock'}
                      ]


async def async_setup(hass, config):
    hass.data[DOMAIN] = []
    # index is the number of client info to find them in the hass.data list
    for index, client in enumerate(config[DOMAIN]):
        client_name = client[CONF_CLIENT_NAME]
        topic = 'monitor/' + client_name + '/'

        # These hass.data will be passed to the sensors
        hass.data[DOMAIN].append({'client_name': client_name, 'topic': topic, 'inbox_information': deepcopy(inbox_information),
                                  'outbox_information': outbox_information, 'last_message_time': None})

        # Load the sensors - that receive and manage clients messages
        hass.async_create_task(
            async_load_platform(
                hass, SENSOR_DOMAIN, DOMAIN, index,  config
            )
        )

        # Load the scripts - that send tommands to the client
        hass.async_create_task(
            async_load_platform(
                hass, SWITCH_DOMAIN, DOMAIN, index,  config
            )
        )

        hass.async_create_task(
            async_load_platform(
                hass, BINARY_SENSOR_DOMAIN, DOMAIN, index,  config
            )
        )

    def update(call=None):
        """Mqtt updates automatically when messages arrive"""
        pass

    hass.services.async_register(DOMAIN, "monitor", update)

    return True
