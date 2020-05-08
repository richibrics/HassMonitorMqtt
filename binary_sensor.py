import logging
import datetime

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.mqtt.debug_info import log_messages

from homeassistant.components.mqtt import (
    ATTR_DISCOVERY_HASH,
    CONF_QOS,
    CONF_STATE_TOPIC,
    CONF_UNIQUE_ID,
    MqttAttributes,
    MqttAvailability,
    MqttDiscoveryUpdate,
    MqttEntityDeviceInfo,
    subscription,
)

from homeassistant.const import STATE_OFF, STATE_ON

OFF_WAIT = 60  # If after X seconds, I don't receive a message, I set the binary sensor to OFF

DEPENDENCIES = ["mqtt"]

MAIN_DOMAIN = "monitor_mqtt"
DOMAIN = "monitor_mqtt_binary_sensor"
DATA_UPDATED = f"{DOMAIN}_data_updated"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info):
    """Set up the sensors."""
    topic = hass.data[MAIN_DOMAIN]['topic']
    inbox_information = hass.data[MAIN_DOMAIN]['inbox_information']
    client_name = hass.data[MAIN_DOMAIN]['client_name']
    async_add_entities(
        [MqttSensor(hass, config, topic, inbox_information, client_name)])

"""This sensor checks if the client is sending (with last_message time) and reports the computer state"""


class MqttSensor(BinarySensorDevice, RestoreEntity):

    def __init__(self, hass, config, topic, inbox_information, client_name):
        """Initialize the sensor."""
        self.hass = hass
        self._config = config
        self.on_icon = 'mdi:lightbulb-on'
        self.off_icon = 'mdi:lightbulb-off'
        self.client_name = client_name
        self._name = "State"
        self.entity_id = MAIN_DOMAIN + '.' + client_name.lower() + '_state'
        self.power = False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.client_name

    @property
    def icon(self):
        if self.is_on:
            return self.on_icon
        else:
            return self.off_icon

    @property
    def _entity_id(self):
        """Return the name of the sensor."""
        return self.entity_id

    @property
    def is_on(self):
        """Return the state of the device."""
        return self.power

    def update(self):
        """ Manage power by last message time """
        last_message_time = self.hass.data[MAIN_DOMAIN]['last_message_time']  # It's like 2020-05-08 11:01:01
        if(last_message_time != None):
            # Parse time format
            last_message_time = datetime.datetime.strptime(
                last_message_time, '%Y-%m-%d %H:%M:%S')
            if((datetime.datetime.now() - last_message_time).total_seconds() >= OFF_WAIT):
                self.power = False  # No more connected
            else:
                self.power = True  # Is sending messages
        else:
            self.power = False  # Mqtt never received information

