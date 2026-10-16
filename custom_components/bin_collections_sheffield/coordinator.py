from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import API_URL, CONF_UPRN, COUNCIL_ID, DOMAIN, SCAN_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class SheffieldBinsApiError(Exception):
    """The council API couldn't be reached or returned something unexpected."""


@dataclass
class BinService:
    name: str
    color: str | None
    group: str | None
    dates: list[date] = field(default_factory=list)

    def next_collection(self, today: date) -> date | None:
        return next((d for d in self.dates if d >= today), None)


async def async_fetch_collections(
    session: aiohttp.ClientSession, uprn: str
) -> dict[str, BinService]:
    """Fetch every scheduled collection for a UPRN, grouped by bin."""
    try:
        async with session.post(
            API_URL,
            json={"councilId": COUNCIL_ID, "uprn": uprn},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status != 200:
                raise SheffieldBinsApiError(f"API returned HTTP {response.status}")

            data = await response.json(content_type=None)

        records = data["data"][0]["records"]
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        raise SheffieldBinsApiError(f"Error communicating with API: {err}") from err
    except (KeyError, IndexError, TypeError) as err:
        raise SheffieldBinsApiError(f"Unexpected API response: {err!r}") from err

    services: dict[str, BinService] = {}

    for record in records:
        try:
            name = record["service"]
            scheduled = dt_util.parse_datetime(record["actual_scheduled_date"])
        except (KeyError, TypeError):
            continue

        if not name or scheduled is None:
            continue

        # The API returns UTC timestamps; convert to local time before taking
        # the date so a BST midnight (23:00Z the day before) lands on the right day.
        collection_date = dt_util.as_local(scheduled).date()

        service = services.setdefault(
            name,
            BinService(
                name=name,
                color=record.get("service_color"),
                group=record.get("service_group"),
            ),
        )
        service.dates.append(collection_date)

    for service in services.values():
        service.dates = sorted(set(service.dates))

    return services


class SheffieldBinsCoordinator(DataUpdateCoordinator[dict[str, BinService]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.uprn = entry.data[CONF_UPRN]

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(hours=SCAN_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, BinService]:
        try:
            return await async_fetch_collections(
                async_get_clientsession(self.hass), self.uprn
            )
        except SheffieldBinsApiError as err:
            raise UpdateFailed(str(err)) from err
