
import logging
import re
import sys
from subprocess import check_output, CalledProcessError

import voluptuous as vol

import homeassistant.loader as loader
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
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

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "monitor-mqtt"
# List of integration names (string) your integration depends upon.
DEPENDENCIES = ["mqtt"]


CONF_CLIENT_NAME = "client_name"
DEFAULT_CLIENT_NAME = "computer"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_NAME,default=DEFAULT_CLIENT_NAME): cv.string
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)



arguments = [{'name': 'ram_used_percentage', 'sensor_label': 'Ram used percentage', 'unity': '%'},
             {'name': 'cpu_used_percentage',
                 'sensor_label': 'Cpu used percentage', 'unity': '%'},
             {'name': 'disk_used_percentage',
                 'sensor_label': 'Disk used percentage', 'unity': '%'},
             {'name': 'operating_system',
                 'sensor_label': 'Operating system', 'unity': ''},
             {'name': 'message_time', 'sensor_label': 'Last update time', 'unity': ''}]


async def async_setup(hass, config):
    """Set up the Speedtest sensor."""

    # These hass.data will be passed to the sensors
    hass.data[DOMAIN] = {'data':None,'arguments':None}
    hass.data[DOMAIN]['data'] = MQTTdata(hass, config)
    hass.data[DOMAIN]['arguments'] = arguments
    # hass.data[DOMAIN] = MQTTdata(hass, conf)


    def update(call=None):
        """(MqttData updates automatically when messages arrive)"""
        pass

    hass.services.async_register(DOMAIN, "monitor", update)

    hass.async_create_task(
        async_load_platform(
            hass, SENSOR_DOMAIN, DOMAIN,None,  config
        )
    )

    return True

class MQTTdata(object):
    # Get data from mqtt and return to the manager of sensors
    data = []

    def __init__(self, hass, config):
        """Initialize the data object."""
        self._config=config
        self.hass=hass
        self.mqtt = hass.components.mqtt
        self.client_name = config[DOMAIN].get(
            CONF_CLIENT_NAME)
        self.topic = 'monitor/' + self.client_name + '/'
        self._sub_state = None
        hass.async_create_task(self._subscribe_topics())

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""
        topics = {}
        
        @callback
        @log_messages(self.hass, self.entity_id)
        def message_received(msg):
            """Handle new MQTT messages."""
            print(msg)
            # Update data row in the list with the topic message
            for info in self.data:
                if True:#msg.startswith(info['name']):
                    info['value'] = msg#msg[len(info['name'])+1:] # Cut the value
                    print(info['value'])

        for argument in arguments:
            print(self.topic+argument['name'])
            self.data.append({'name': argument['name'], 'value': None})
            topics[argument['name']]= {
                    'topic': self.topic+argument['name'],
                    'msg_callback': message_received,
                    'qos': 0,
                }

        self._sub_state = await subscription.async_subscribe_topics(self.hass,self._sub_state,topics)