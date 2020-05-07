import logging

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
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

DEPENDENCIES = ["mqtt"]

MAIN_DOMAIN = "monitor-mqtt"
DOMAIN ="monitor-mqtt-sensor"
DATA_UPDATED = f"{DOMAIN}_data_updated"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info):
    """Set up the sensors."""
    topic = hass.data[MAIN_DOMAIN]['topic']
    arguments = hass.data[MAIN_DOMAIN]['arguments']
    async_add_entities([MqttSensor(hass, config, topic, argument) for argument in arguments])


class MqttSensor(RestoreEntity):
    """Implementation of a speedtest.net sensor."""

    def __init__(self, hass,config, topic, argument):
        """Initialize the sensor."""
        self._config=config
        self.info = argument
        self.topic=topic+argument['name']
        self._name = argument['sensor_label']
        self.entity_id = 'monitor.' + argument['name']
        self._unit_of_measurement = argument['unity']
        self.mqtt = hass.components.mqtt
        self.value = None
        self._state = None 
        self._sub_state=None

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format('Monitor: ', self._name)

    @property
    def _entity_id(self):
        """Return the name of the sensor."""
        return self._entity_id

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        """Value is auto-updated from mqtt callback"""
        self._state=self.value

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        await super().async_added_to_hass()
        await self._subscribe_topics()
    

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

    
    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""
        print(self.topic)
        @callback
        #@log_messages(self.hass, self._entity_id)
        def message_received(msg):
            """Handle new MQTT messages."""
            payload = msg.payload

            self.value = payload
            self.async_write_ha_state()

        self._sub_state = await subscription.async_subscribe_topics(
            self.hass,
            self._sub_state,
            {
                "state_topic": {
                    "topic": self.topic,
                    "msg_callback": message_received,
                    "qos":0,# self._config[CONF_QOS],
                }
            },
        )