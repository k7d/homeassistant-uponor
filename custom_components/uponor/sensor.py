from homeassistant.components.sensor import (SensorDeviceClass)
from homeassistant.const import (UnitOfTemperature, PERCENTAGE)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from logging import getLogger
from .const import (
    DOMAIN,
    SIGNAL_UPONOR_STATE_UPDATE,
    DEVICE_MANUFACTURER,
)


_LOGGER = getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    state_proxy = hass.data[DOMAIN]["state_proxy"]

    entities = []
    for thermostat in hass.data[DOMAIN]["thermostats"]:
        if thermostat.lower() in config_entry.data:
            room_name = config_entry.data[thermostat.lower()]
        else:
            room_name = state_proxy.get_room_name(thermostat)
        entities.append(UponorThermostatTemperatureSensor(state_proxy, thermostat, room_name))
        entities.append(UponorThermostatHumiditySensor(state_proxy, thermostat, room_name))
    if entities:
        async_add_entities(entities, update_before_add=False)

class UponorSensor(Entity):
    def __init__(self, state_proxy, thermostat, room_name):
        self._state_proxy = state_proxy
        self._thermostat = thermostat
        self._room_name = room_name
        self._available = False

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        async_dispatcher_connect(self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback)

    @callback
    def _update_callback(self):
        self.async_schedule_update_ha_state(True)
        self._available = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._state_proxy.get_thermostat_id(self._thermostat)}")},
            "name": self._room_name,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": self._state_proxy.get_model(),
            "sw_version": self._state_proxy.get_version(self._thermostat)
        }

    @property
    def available(self):
        return self._available


class UponorThermostatTemperatureSensor(UponorSensor):
    @property
    def unique_id(self):
        return f"{self._state_proxy.get_thermostat_id(self._thermostat)}_temperature"

    @property
    def name(self):
        return f"{self._room_name} Temperature"

    @property
    def icon(self):
        return 'mdi:thermometer'

    # ** Static **
    @property
    def unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    # ** State **
    @property
    def state(self):
        return self._state_proxy.get_temperature(self._thermostat)


class UponorThermostatHumiditySensor(UponorSensor):
    @property
    def unique_id(self):
        return f"{self._state_proxy.get_thermostat_id(self._thermostat)}_humidity"

    @property
    def name(self):
        return f"{self._room_name} Humidity"

    @property
    def icon(self):
        return 'mdi:water-percent'

    @property
    def available(self):
        return self._available

    # ** Static **
    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def device_class(self):
        return SensorDeviceClass.HUMIDITY

    # ** State **
    @property
    def state(self):
        return self._state_proxy.get_humidity(self._thermostat)
