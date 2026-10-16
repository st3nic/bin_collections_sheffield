from __future__ import annotations

from datetime import date, datetime, time, timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_REMINDER_TIME,
    DEFAULT_REMINDER_TIME,
    REMINDER_OFF_TIME,
)
from .coordinator import SheffieldBinsCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    reminder_time = dt_util.parse_time(
        entry.options.get(CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME)
    )

    async_add_entities([BinsOutTonightSensor(entry.runtime_data, reminder_time)])


class BinsOutTonightSensor(CoordinatorEntity[SheffieldBinsCoordinator], BinarySensorEntity):
    """On from the reminder time the evening before a collection until collection morning."""

    _attr_name = "Bins out tonight"
    _attr_icon = "mdi:delete-alert"

    def __init__(self, coordinator: SheffieldBinsCoordinator, reminder_time: time):
        super().__init__(coordinator)

        self._reminder_time = reminder_time
        self._unsub_timer: CALLBACK_TYPE | None = None
        self._bins: list[str] = []
        self._collection_date: date | None = None

        self._attr_unique_id = f"{coordinator.uprn}_bins_out_tonight"

    def _local(self, day: date, at: time) -> datetime:
        return datetime.combine(day, at, tzinfo=dt_util.get_default_time_zone())

    def _window(self, collection_date: date) -> tuple[datetime, datetime]:
        return (
            self._local(collection_date - timedelta(days=1), self._reminder_time),
            self._local(collection_date, REMINDER_OFF_TIME),
        )

    @callback
    def _async_update_state(self, *_args) -> None:
        """Work out which bins are due now and when the state next changes."""
        now = dt_util.now()

        self._bins = []
        self._collection_date = None
        next_change: datetime | None = None

        for service in self.coordinator.data.values():
            for collection_date in service.dates:
                start, end = self._window(collection_date)

                if start <= now < end:
                    self._bins.append(service.name)
                    self._collection_date = collection_date

                for boundary in (start, end):
                    if boundary > now and (next_change is None or boundary < next_change):
                        next_change = boundary

        self._bins.sort()

        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

        if next_change is not None:
            self._unsub_timer = async_track_point_in_time(
                self.hass, self._async_timer_fired, next_change
            )

    @callback
    def _async_timer_fired(self, _now: datetime) -> None:
        self._unsub_timer = None
        self._async_update_state()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        self._async_update_state()

        self.async_on_remove(self._async_cancel_timer)

    @callback
    def _async_cancel_timer(self) -> None:
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._async_update_state()
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool:
        return bool(self._bins)

    @property
    def extra_state_attributes(self):
        return {
            "bins": self._bins,
            "collection_date": (
                self._collection_date.isoformat() if self._collection_date else None
            ),
        }
