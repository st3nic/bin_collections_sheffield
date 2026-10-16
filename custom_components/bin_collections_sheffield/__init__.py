from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change

from .const import CONF_UPRN
from .coordinator import SheffieldBinsCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SENSOR]

LEGACY_UNIQUE_ID_PREFIX = "sheffield_bins_"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    uprn = entry.data[CONF_UPRN]

    # Entries created before 2.0.0 have no unique ID, so the same UPRN could be added twice.
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=uprn)

    await _async_migrate_unique_ids(hass, entry, uprn)

    coordinator = SheffieldBinsCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # "Tomorrow" should become "Today" at midnight, not at the next API poll.
    @callback
    def _async_midnight(_now):
        coordinator.async_update_listeners()

    entry.async_on_unload(
        async_track_time_change(hass, _async_midnight, hour=0, minute=0, second=0)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_migrate_unique_ids(hass: HomeAssistant, entry: ConfigEntry, uprn: str):
    """Move pre-2.0.0 sensors (sheffield_bins_black_bin) onto the new per-UPRN IDs.

    This keeps existing entity IDs such as sensor.black_bin_collection, along
    with their history and any dashboard cards that use them.
    """

    @callback
    def _migrate(entity_entry: er.RegistryEntry):
        if not entity_entry.unique_id.startswith(LEGACY_UNIQUE_ID_PREFIX):
            return None

        slug = entity_entry.unique_id.removeprefix(LEGACY_UNIQUE_ID_PREFIX)

        return {"new_unique_id": f"{uprn}_{slug}_collection"}

    await er.async_migrate_entries(hass, entry.entry_id, _migrate)
