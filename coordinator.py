"""Coordinator for Adaptive Day Cycle."""

from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from astral import LocationInfo
from astral.location import Location
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EARLIEST_DAWN,
    CONF_NIGHT_START,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_WEATHER_ENTITY,
)
from .dc_calculations import (
    calculate_daycycle,
    EnvironmentalConditions,
)


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

    async def _async_update_data(self):
        """Update day cycle data."""

        now = dt_util.now()

        latitude = self.entry.data[CONF_LATITUDE]
        longitude = self.entry.data[CONF_LONGITUDE]

        location_info = LocationInfo(
            name=self.entry.title,
            region="ADC",
            timezone=self.hass.config.time_zone,
            latitude=latitude,
            longitude=longitude,
        )

        astral_location = Location(location_info)
        elevation = 0

        sunrise = await self.hass.async_add_executor_job(
            lambda: astral_location.sunrise(
                now.date(),
                local=True,
                observer_elevation=elevation,
            )
        )

        sunset = await self.hass.async_add_executor_job(
            lambda: astral_location.sunset(
                now.date(),
                local=True,
                observer_elevation=elevation,
            )
        )

        earliest_dawn = datetime.strptime(
            self.entry.data[CONF_EARLIEST_DAWN],
            "%H:%M",
        ).time()

        night_start = datetime.strptime(
            self.entry.data[CONF_NIGHT_START],
            "%H:%M",
        ).time()



        weather_entity = self.entry.data.get(
            CONF_WEATHER_ENTITY,
        )

        conditions = None

        if weather_entity:
            weather_state = self.hass.states.get(
                weather_entity,
            )

            if weather_state:
                attributes = weather_state.attributes

                conditions = EnvironmentalConditions(
                    condition=weather_state.state,
                    cloud_coverage=attributes.get(
                        "cloud_coverage"
                    ),
                    precipitation=attributes.get(
                        "precipitation"
                    ),
                    illuminance=attributes.get(
                        "illuminance"
                    ),
                )

                """LOGGER.warning(
                    (
                        "ADC Weather | "
                        "Entity: %s | "
                        "Condition: %s | "
                        "Clouds: %s | "
                        "Precipitation: %s | "
                        "Illuminance: %s"
                    ),
                    weather_entity,
                    conditions.condition,
                    conditions.cloud_coverage,
                    conditions.precipitation,
                    conditions.illuminance,
                )"""

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
