from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .coordinator import SheffieldBinsCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SheffieldBinsCalendar(entry.runtime_data)])


class SheffieldBinsCalendar(CoordinatorEntity[SheffieldBinsCoordinator], CalendarEntity):
    """All collections for an address as all-day events, one per bin."""

    _attr_name = "Bin Collections"
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator: SheffieldBinsCoordinator):
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.uprn}_calendar"

    def _events(self) -> list[CalendarEvent]:
        events = [
            CalendarEvent(
                start=collection_date,
                end=collection_date + timedelta(days=1),
                summary=service.name,
            )
            for service in self.coordinator.data.values()
            for collection_date in service.dates
        ]

        return sorted(events, key=lambda event: (event.start, event.summary))

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()

        return next((e for e in self._events() if e.start >= today), None)

    async def async_get_events(
        self, hass, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            event
            for event in self._events()
            if event.start_datetime_local < end_date
            and event.end_datetime_local > start_date
        ]
