from typing import final


from ...common.base import Instrument
from .system_settings import SystemSettings


@final
class SpectrumAnalyser(Instrument):
    def __init__(
        self,
        address: str,
        instrument_name: str = "SSA3075X-R",
        instrument_mode: str = "SA",
        query_delay: float = 0.25,
    ) -> None:

        super().__init__(address, instrument_name, query_delay)

        self.system: SystemSettings = SystemSettings(instrument=self)
        self.system.instrument_mode = instrument_mode

        if self.system.instrument_mode == "SA":
            from .sa_freq import SAFreq

            self.freq: SAFreq = SAFreq(instrument=self)
