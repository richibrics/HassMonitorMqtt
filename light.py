
import logging
import datetime
import collections

from .funcs import GetOSicon
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.components.mqtt.light.schema_basic import MqttLight
from homeassistant.components.camera import STATE_IDLE, STATE_STREAMING
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
DOMAIN = "monitor_mqtt_camera"
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info):
    # In discovery info I have the client ID
    """Set up the sensors."""
    client_index = discovery_info
    topic = hass.data[MAIN_DOMAIN]['data'][client_index]['topic']
    light_information = hass.data[MAIN_DOMAIN]['data'][client_index]['light_information']
    client_name = hass.data[MAIN_DOMAIN]['data'][client_index]['client_name']

    light_config = collections.OrderedDict({'platform': 'mqtt', 'command_topic': topic+light_information['set_topic'], 'brightness_command_topic': topic+light_information['set_topic'], 'brightness_state_topic': topic+light_information['get_topic'], 'brightness_scale': 100,
                                            'schema': 'basic', 'payload_not_available': 'offline', 'retain': False, 'on_command_type': 'last', 'white_value_scale': 100, 'optimistic': False, 'name': '', 'qos': 0, 'payload_on': 'ON', 'payload_off': 'OFF', 'payload_available': 'online', 'state_value_template': None})

    async_add_entities(
        [MonitorLight(hass, light_config, light_information, client_index, client_name)])

    # Create a MQTT camera passing the proper config


class MonitorLight(MqttLight):

    def __init__(self, hass, light_config, light_info, client_index, client_name):
        """Initialize the sensor."""
        MqttLight.__init__(self, light_config, 0, None)
        self.client_index = client_index
        self.client_name = client_name
        self.light_info = light_info
        self._name = client_name + ' - ' + light_info['light_label']
        self.hass = hass
        self.entity_id = MAIN_DOMAIN + '.' + client_name.lower() + '_' + \
            light_info['id']

        print(self._topic)

    @property
    def icon(self):
        return self.light_info['icon']

    @property
    def name(self):
        return self._name