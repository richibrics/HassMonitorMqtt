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

MAIN_DOMAIN = "monitor_mqtt"
DOMAIN = "monitor_mqtt_sensor"
DATA_UPDATED = f"{DOMAIN}_data_updated"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info):
    # In discovery info I have the client ID
    """Set up the sensors."""
    client_index = discovery_info
    topic = hass.data[MAIN_DOMAIN][client_index]['topic']
    inbox_information = hass.data[MAIN_DOMAIN][client_index]['inbox_information']
    client_name = hass.data[MAIN_DOMAIN][client_index]['client_name']
    async_add_entities([MqttSensor(hass, config, topic, info, client_index, client_name)
                        for info in inbox_information])


class MqttSensor(RestoreEntity):

    def __init__(self, hass, config, topic, inbox_info, client_index, client_name):
        """Initialize the sensor."""
        self._config = config
        self.client_index = client_index
        self.client_name = client_name
        self.inbox_info = inbox_info
        self.topic = topic+inbox_info['name']
        self._name = inbox_info['sensor_label']
        self.entity_id = MAIN_DOMAIN + '.' + client_name.lower() + '_' + \
            inbox_info['id']
        self._unit_of_measurement = inbox_info['unity']
        self.mqtt = hass.components.mqtt
        self.value = None
        self._state = None
        self._sub_state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        icon = self.inbox_info['icon']
        # If I have this info in the icon then I am in the topic where I recive the OS
        if('$OPERATING_SYSTEM' in icon):  # CHange the icon with the OS customized icon
            new_icon = 'collage'  # Default if OS not known
            if(self.state == 'Windows'):
                new_icon = 'microsoft-windows'
            elif(self.state == 'Linux'):
                new_icon = 'penguin'
            elif(self.state == 'macOS'):
                new_icon = 'apple'
            icon = icon.replace('$OPERATING_SYSTEM',
                                new_icon)  # Set the icon name
        return icon

    @property
    def _entity_id(self):
        """Return the name of the sensor."""
        return self.entity_id

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
        self._state = self.value

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        await super().async_added_to_hass()
        await self._subscribe_topics()

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""
        # print(self.topic)
        @callback
        # @log_messages(self.hass, self._entity_id)
        def message_received(msg):
            """Handle new MQTT messages."""
            payload = msg.payload
            self.value = payload
            self.async_write_ha_state()
            # If message is last-time, save it to pass to the monitor state binary sensor
            if self.inbox_info['name'] == 'message_time':
                self.hass.data[MAIN_DOMAIN][self.client_index]['last_message_time'] = payload

        self._sub_state = await subscription.async_subscribe_topics(
            self.hass,
            self._sub_state,
            {
                "state_topic": {
                    "topic": self.topic,
                    "msg_callback": message_received,
                    "qos": 0,  # self._config[CONF_QOS],
                }
            },
        )
