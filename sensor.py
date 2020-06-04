import logging
import json

from .funcs import GetOSicon
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.mqtt.debug_info import log_messages
from homeassistant.components.homeassistant import DOMAIN as HA_DOMAIN

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
        self.hass=hass
        self.entity_id = MAIN_DOMAIN + '.' + client_name.lower() + '_' + \
            inbox_info['id']
        self._unit_of_measurement = inbox_info['unity']
        self.mqtt = hass.components.mqtt
        self.value = None
        self._state = None
        self._sub_state = None

    @property
    def device_class(self):
        return self.inbox_info['device_class']

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        if self.device_class is None:
            icon = self.inbox_info['icon']
            # Customize for power cable
            if '$PLUGGED' in icon:
                icon = icon.replace('$PLUGGED', 'power-plug')
                if self.state is False:
                    icon = icon + '-off'
            # If I have this info in the icon then I am in the topic where I recive the OS
            if('$OPERATING_SYSTEM' in icon):  # CHange the icon with the OS customized icon
                icon = icon.replace('$OPERATING_SYSTEM', GetOSicon(
                    self.state))  # Set the icon name
            return icon
        else:
            return ''

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

    def set_unavailable(self):
        """Set state to UNAVAILABLE."""
        self._is_available = False
        self.async_write_ha_state()

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""
        # print(self.topic)
        @callback
        # @log_messages(self.hass, self._entity_id)
        async def message_received(msg):
            """Handle new MQTT messages."""
            payload = msg.payload
            # Save the new value
            self.value = payload

            # Set to unavailable if paylod is 'None' (used for battery sensors)
            if(payload == 'None'):
                self.set_unavailable()

            if payload == 'False':
                self.value = False
            elif payload == 'True':
                self.value = True

            try:
                if 'cpu_temperature' in self._entity_id and len(payload) > 0:
                    # Then make an average of the cores temperatures
                    # convert json to list
                    temps=json.loads(payload)
                    temp=sum(temps)/len(temps)
                    self.value=temp
            except:
                pass

            # Save also in the inbox-info list
            self.inbox_info['value']=self.value

            self.async_write_ha_state()

        self._sub_state=await subscription.async_subscribe_topics(
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
