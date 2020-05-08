import logging

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.mqtt.debug_info import log_messages

from homeassistant.const import STATE_OFF, STATE_ON
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
DOMAIN = "monitor_mqtt_switch"
DATA_UPDATED = f"{DOMAIN}_data_updated"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info):
    """Set up the sensors."""
    topic = hass.data[MAIN_DOMAIN]['topic']
    outbox_information = hass.data[MAIN_DOMAIN]['outbox_information']
    client_name = hass.data[MAIN_DOMAIN]['client_name']
    async_add_entities([MqttSwitch(hass, config, topic, info, client_name)
                        for info in outbox_information])


class MqttSwitch(
        ToggleEntity,
        RestoreEntity,):

    def __init__(self, hass, config, topic, outbox_info, client_name):
        self.hass = hass
        self.client_name = client_name
        self._config = config
        self.outbox_info = outbox_info
        self.topic = topic+outbox_info['name']
        self._name = outbox_info['sensor_label']
        self.entity_id = MAIN_DOMAIN + '.' + client_name.lower() + '_' + outbox_info['id']
        self.mqtt = hass.components.mqtt
        self._state = None
        self._state_on = False
        self._state_off = True
        # Always set to off cause, currently commands are only to power on (like scripts)
        self._state = False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        return self.outbox_info['icon']

    @property
    def _entity_id(self):
        """Return the name of the script."""
        return self.entity_id

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.entity_id

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        await super().async_added_to_hass()

    async def async_turn_on(self, **kwargs):
        await self.SendCommand('ON')

    async def async_turn_off(self, **kwargs):
        await self.SendCommand('OFF')

    async def SendCommand(self, payload):
        self.mqtt.async_publish(self.topic, payload)
