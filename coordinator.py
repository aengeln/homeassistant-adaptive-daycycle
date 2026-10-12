"""Coordinator for Adaptive Day Cycle."""

from __future__ import annotations

from datetime import timedelta
import logging

from astral import LocationInfo
from astral.location import Location

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EARLIEST_DAWN,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NIGHT_START,
    CONF_WEATHER_ENTITY,
    DEFAULT_EARLIEST_DAWN,
    DEFAULT_NIGHT_START,
)
from .dc_calculations import (
    EnvironmentalConditions,
    calculate_daycycle,
)

LOGGER = logging.getLogger(__name__)


class AdaptiveDayCycleCoordinator(DataUpdateCoordinator):
    """Coordinator for Adaptive Day Cycle."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            logger=LOGGER,
            name="Adaptive Day Cycle",
            update_interval=timedelta(minutes=5),
        )

        self.entry = entry

    @property
    def settings(self) -> dict:
        """Return entry data overridden by options."""
        return {**self.entry.data, **self.entry.options}

    async def _async_update_data(self):
        """Update day cycle data."""

        settings = self.settings
        now = dt_util.now()

        latitude = settings[CONF_LATITUDE]
        longitude = settings[CONF_LONGITUDE]

        location_info = LocationInfo(
            name=self.entry.title,
            region="ADC",
            timezone=self.hass.config.time_zone,
            latitude=latitude,
            longitude=longitude,
        )
        astral_location = Location(location_info)

        try:
            sunrise = astral_location.sunrise(now.date(), local=True)
            sunset = astral_location.sunset(now.date(), local=True)
        except ValueError:
            # Polar day/night: the sun neither rises nor sets. Fall back to a
            # symmetric day around solar noon.
            noon = astral_location.noon(now.date(), local=True)
            sunrise = noon - timedelta(hours=6)
            sunset = noon + timedelta(hours=6)

        earliest_dawn = dt_util.parse_time(
            settings.get(CONF_EARLIEST_DAWN, DEFAULT_EARLIEST_DAWN)
        )
        night_start = dt_util.parse_time(
            settings.get(CONF_NIGHT_START, DEFAULT_NIGHT_START)
        )

        conditions = None
        weather_entity = settings.get(CONF_WEATHER_ENTITY)

        if weather_entity:
            weather_state = self.hass.states.get(weather_entity)

            if weather_state:
                attributes = weather_state.attributes

                conditions = EnvironmentalConditions(
                    condition=weather_state.state,
                    cloud_coverage=attributes.get("cloud_coverage"),
                    precipitation=attributes.get("precipitation"),
                    illuminance=attributes.get("illuminance"),
                )

        return calculate_daycycle(
            now=now,
            sunrise=sunrise,
            sunset=sunset,
            earliest_dawn=earliest_dawn,
            night_start=night_start,
            morning_conditions=conditions,
            dusk_conditions=conditions,
            evening_conditions=conditions,
            latitude=latitude,
        )
