from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


BIN_TYPES = [
    "Black Bin",
    "Blue Bin",
    "Brown Bin",
    "Green Bin",
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    for bin_type in BIN_TYPES:
        entities.append(
            SheffieldBinSensor(coordinator, bin_type)
        )

    async_add_entities(entities)


class SheffieldBinSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, bin_type):
        super().__init__(coordinator)

        self.bin_type = bin_type

        self._attr_name = f"{bin_type} Collection"
        self._attr_unique_id = f"sheffield_bins_{bin_type.lower().replace(' ', '_')}"
        self._attr_icon = "mdi:trash-can"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.bin_type)

        if not data:
            return None
        elif data["days_until"] == 0:
            return "Today"
        else:
            return data["days_until"]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.bin_type)

        if not data:
            return {}

        return {
            "next_collection_date": data["date"],
            "bin_type": self.bin_type,
            "days_until": data["days_until"],
            "service_group": data["group"],
            "color": data["color"],
        }

    @property
    def unit_of_measurement(self):
        data = self.coordinator.data.get(self.bin_type)
        
        if data["days_until"] > 1:
            return "days"
        elif data["days_until"] == 1:
            return "day"
        elif data["days_until"] == 0:
            return " "
