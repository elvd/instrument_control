"""Sweep functionality for Siglent SSG5060X-V

Implements various frequency and amplitude sweeps - list, step, linear, and
logarithmic. These are all triggered internally and there is no software sync
over the VISA connection.
"""

from __future__ import annotations

from .cw import SignalGenerator


class Sweep(SignalGenerator):
    def __init__(
        self,
        address: str | int,
        instrument_name: str = "sweep",
        query_delay: float = 0.25,
        sweep_type: str = "FREQ",
    ) -> None:
        super().__init__(address, instrument_name, query_delay)
        self.sweep_type: str = sweep_type
