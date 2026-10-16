from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util, slugify

from .const import DOMAIN, MANUFACTURER
from .coordinator import BinService, SheffieldBinsCoordinator


def _days_until(next_date: date | None, today: date) -> int | None:
    if next_date is None:
        return None

    return (next_date - today).days


def _friendly(next_date: date | None, today: date) -> str | None:
    days = _days_until(next_date, today)

    if days is None:
        return None
    elif days == 0:
        return "Today"
    elif days == 1:
        return "Tomorrow"
    else:
        return f"In {days} days"


@dataclass(frozen=True, kw_only=True)
class SheffieldBinSensorDescription(SensorEntityDescription):
    value_fn: Callable[[date | None, date], str | int | date | None]


SENSORS = (
    # Keeps the "collection" key so pre-2.0.0 sensors migrate onto it.
    SheffieldBinSensorDescription(
        key="collection",
        name="Collection",
        icon="mdi:trash-can",
        value_fn=_friendly,
    ),
    SheffieldBinSensorDescription(
        key="days_until",
        name="Days until",
        icon="mdi:calendar-clock",
        native_unit_of_measurement=UnitOfTime.DAYS,
        value_fn=_days_until,
    ),
    SheffieldBinSensorDescription(
        key="next_collection",
        name="Next collection",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda next_date, today: next_date,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SheffieldBinsCoordinator = entry.runtime_data

    known_bins: set[str] = set()

    # Only create sensors for bins the council actually collects from this
    # address, and pick up any new ones that appear in a later update.
    @callback
    def _async_add_new_bins():
        new_bins = [name for name in coordinator.data if name not in known_bins]

        if not new_bins:
            return

        known_bins.update(new_bins)

        async_add_entities(
            SheffieldBinSensor(coordinator, bin_name, description)
            for bin_name in new_bins
            for description in SENSORS
        )

    _async_add_new_bins()

    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_bins))


class SheffieldBinSensor(CoordinatorEntity[SheffieldBinsCoordinator], SensorEntity):
    _attr_has_entity_name = True

    entity_description: SheffieldBinSensorDescription

    def __init__(
        self,
        coordinator: SheffieldBinsCoordinator,
        bin_name: str,
        description: SheffieldBinSensorDescription,
    ):
        super().__init__(coordinator)

        self.entity_description = description
        self.bin_name = bin_name

        bin_slug = slugify(bin_name)

        self._attr_unique_id = f"{coordinator.uprn}_{bin_slug}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.uprn}_{bin_slug}")},
            name=bin_name,
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _service(self) -> BinService | None:
        return self.coordinator.data.get(self.bin_name)

    @property
    def available(self) -> bool:
        return super().available and self._service is not None

    @property
    def native_value(self):
        today = dt_util.now().date()

        return self.entity_description.value_fn(
            self._service.next_collection(today), today
        )

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "collection":
            return None

        service = self._service
        today = dt_util.now().date()
        next_date = service.next_collection(today)

        return {
            "next_collection_date": next_date.isoformat() if next_date else None,
            "bin_type": self.bin_name,
            "days_until": _days_until(next_date, today),
            "service_group": service.group,
            "color": service.color,
        }
