"""Sensor platform for Adaptive Day Cycle."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType

from .coordinator import AdaptiveDayCycleCoordinator
from .dc_calculations import (
    PHASE_AFTERNOON,
    PHASE_DAWN,
    PHASE_DUSK,
    PHASE_EVENING,
    PHASE_MORNING,
    PHASE_NIGHT,
)

PHASE_OPTIONS = [
    PHASE_DAWN,
    PHASE_MORNING,
    PHASE_AFTERNOON,
    PHASE_DUSK,
    PHASE_EVENING,
    PHASE_NIGHT,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Adaptive Day Cycle sensor entities."""

    coordinator: AdaptiveDayCycleCoordinator = hass.data[
        "adaptive_daycycle"
    ][entry.entry_id]

    async_add_entities(
        [
            AdaptiveDayPhaseSensor(coordinator, entry),
            AdaptiveDayTimeSensor(coordinator, entry, PHASE_DAWN),
            AdaptiveDayTimeSensor(coordinator, entry, PHASE_MORNING),
            AdaptiveDayTimeSensor(coordinator, entry, PHASE_AFTERNOON),
            AdaptiveDayTimeSensor(coordinator, entry, PHASE_DUSK),
            AdaptiveDayTimeSensor(coordinator, entry, PHASE_EVENING),
            AdaptiveDayTimeSensor(coordinator, entry, PHASE_NIGHT),
        ]
    )


class AdaptiveDayPhaseSensor(CoordinatorEntity, SensorEntity):
    """Adaptive Day Cycle phase sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = PHASE_OPTIONS
    _attr_translation_key = "day_phase"

    def __init__(
        self,
        coordinator: AdaptiveDayCycleCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry

        instance_name = entry.title.lower().replace(" ", "_")

        self._attr_unique_id = (
            f"adaptive_daycycle_day_phase_{instance_name}"
        )

        self._attr_name = (
            f"Day Phase {entry.title}"
        )
        self._attr_suggested_object_id = (
            f"day_phase_{instance_name}"
        )
        self._attr_native_value = (
            self.coordinator.data.current_phase
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {
                ("adaptive_daycycle", self._entry.entry_id)
            },
            "name": self._entry.title,
            "manufacturer": "Aengeln",
            "model": "Adaptive Day Cycle",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def native_value(self) -> str:
        """Return the current phase."""
        return self.coordinator.data.current_phase


class AdaptiveDayTimeSensor(CoordinatorEntity, SensorEntity):
    """Adaptive Day Cycle phase start time sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: AdaptiveDayCycleCoordinator,
        entry: ConfigEntry,
        phase: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry

        instance_name = entry.title.lower().replace(" ", "_")

        self._phase = phase

        self._attr_unique_id = (
            f"adaptive_daycycle_{phase}_start_{instance_name}"
        )

        self._attr_name = (
            f"{phase.capitalize()} Start {entry.title}"
        )
        self._attr_suggested_object_id = (
            f"{phase}_start_{instance_name}"
        )

    @property
    def native_value(self):
        """Return the phase start timestamp."""

        return self.coordinator.data.phase_starts[self._phase]
    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {
                ("adaptive_daycycle", self._entry.entry_id)
            },
            "name": self._entry.title,
            "manufacturer": "Aengeln",
            "model": "Adaptive Day Cycle",
            "entry_type": DeviceEntryType.SERVICE,
        }