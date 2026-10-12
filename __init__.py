"""Adaptive Day Cycle integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import AdaptiveDayCycleCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def _async_migrate_unique_ids(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Move title-based unique IDs to entry_id-based ones."""

    instance_name = entry.title.lower().replace(" ", "_")
    old_prefix = "adaptive_daycycle_"
    old_suffix = f"_{instance_name}"

    @callback
    def _migrate(entity_entry: er.RegistryEntry) -> dict | None:
        uid = entity_entry.unique_id
        if uid.startswith(entry.entry_id):
            return None
        if uid.startswith(old_prefix) and uid.endswith(old_suffix):
            key = uid[len(old_prefix) : -len(old_suffix)]
            return {"new_unique_id": f"{entry.entry_id}_{key}"}
        return None

    await er.async_migrate_entries(hass, entry.entry_id, _migrate)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Adaptive Day Cycle from a config entry."""

    await _async_migrate_unique_ids(hass, entry)

    coordinator = AdaptiveDayCycleCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload when options change so new settings take effect.
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after an options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Adaptive Day Cycle config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
