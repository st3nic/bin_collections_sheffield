from __future__ import annotations

from datetime import datetime, timedelta
import logging

import aiohttp
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import API_URL, COUNCIL_ID, DOMAIN, SCAN_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class SheffieldBinsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.uprn = entry.data["uprn"]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=SCAN_INTERVAL_HOURS),
        )

    async def _async_update_data(self):
        payload = {
            "councilId": COUNCIL_ID,
            "uprn": self.uprn,
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30,
                ) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API Error: {response.status}")

                    data = await response.json()

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        records = data["data"][0]["records"]

        now = datetime.utcnow().date()

        next_collections = {}

        for record in records:
            service = record["service"]

            collection_date = datetime.fromisoformat(
                record["actual_scheduled_date"].replace("Z", "+00:00")
            ).date()

            if collection_date < now:
                continue

            if service not in next_collections:
                days_until = (collection_date - now).days

                next_collections[service] = {
                    "date": collection_date.isoformat(),
                    "days_until": days_until,
                    "color": record["service_color"],
                    "group": record["service_group"],
                }

        return next_collections