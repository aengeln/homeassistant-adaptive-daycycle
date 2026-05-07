"""Coordinator for Adaptive Day Cycle."""

from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.sun import get_astral_location
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import CONF_EARLIEST_DAWN, CONF_NIGHT_START
from .dc_calculations import calculate_daycycle


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

        astral_location, elevation = get_astral_location(self.hass)

        sunrise = astral_location.sunrise(
            now.date(),
            local=True,
            observer_elevation=elevation,
        )

        sunset = astral_location.sunset(
            now.date(),
            local=True,
            observer_elevation=elevation,
        )

        earliest_dawn = datetime.strptime(
            self.entry.data[CONF_EARLIEST_DAWN],
            "%H:%M",
        ).time()

        night_start = datetime.strptime(
            self.entry.data[CONF_NIGHT_START],
            "%H:%M",
        ).time()

        return calculate_daycycle(
            now=now,
            sunrise=sunrise,
            sunset=sunset,
            earliest_dawn=earliest_dawn,
            night_start=night_start,
        )
