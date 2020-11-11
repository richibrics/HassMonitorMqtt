import logging
import datetime
import collections

from .funcs import GetOSicon
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.components.mqtt.camera import MqttCamera
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
    camera_information = hass.data[MAIN_DOMAIN]['data'][client_index]['camera_information']
    client_name = hass.data[MAIN_DOMAIN]['data'][client_index]['client_name']

    camera_config = collections.OrderedDict({'topic': topic+camera_information['topic_suffix'], 'platform': 'mqtt', 'payload_available': 'online',
                                             'payload_not_available': 'offline', 'name': camera_information['camera_label'], 'qos': 0})

    async_add_entities(
        [MonitorCamera(hass, camera_config, camera_information, client_index, client_name)])

    # Create a MQTT camera passing the proper config


class MonitorCamera(MqttCamera):

    def __init__(self, hass, camera_config, camera_info, client_index, client_name):
        """Initialize the sensor."""
        MqttCamera.__init__(self, camera_config, 0, None)
        self.client_index = client_index
        self.client_name = client_name
        self.camera_info = camera_info
        self._name = client_name + ' - ' + camera_info['camera_label']
        self.hass = hass
        self.entity_id = MAIN_DOMAIN + '.' + client_name.lower() + '_' + \
            camera_info['id']

    @property
    def icon(self):
        return self.camera_info['icon']

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        """Return true if on."""
        return True if self.hass.states.get(MAIN_DOMAIN + '.' + self.client_name.lower() + '_state').state == 'on' else False

    @property
    def state(self):
        return ''
