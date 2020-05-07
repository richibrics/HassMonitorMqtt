import logging

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

MAIN_DOMAIN = "monitor-mqtt"
DOMAIN ="monitor-mqtt-sensor"
DATA_UPDATED = f"{DOMAIN}_data_updated"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info):
    """Set up the sensors."""
    data = hass.data[MAIN_DOMAIN]['data']
    arguments = hass.data[MAIN_DOMAIN]['arguments']
    async_add_entities([MqttSensor(data, argument) for argument in arguments])


class MqttSensor(RestoreEntity):
    """Implementation of a speedtest.net sensor."""

    def __init__(self, mqtt_data, argument):
        """Initialize the sensor."""
        self.info = argument
        self._name = argument['sensor_label']
        self._entity_id = 'monitor-' + argument['name']
        self._unit_of_measurement = argument['unity']
        self.mqtt_client = mqtt_data
        self._state = None

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
        """Get the latest data and update the states."""
        data = self.mqtt_client.data
        if data:
            # Take value from data
            for info in data:
                if info['name']==self.info['name']:
                    self._state=info['value']

    async def async_added_to_hass(self):
            """Handle entity which will be added."""
            await super().async_added_to_hass()
            state = await self.async_get_last_state()
            if not state:
                return
            self._state = state.state

            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass, DATA_UPDATED, self._schedule_immediate_update
                )
            )
    

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)