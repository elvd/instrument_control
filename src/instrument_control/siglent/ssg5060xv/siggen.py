from ...common.base import Instrument
from .cw import CW
from .sweep import Sweep


class SignalGenerator(Instrument):
    def __init__(
        self,
        address: str,
        instrument_name: str = "SSG5060XV",
        query_delay: float = 0.25,
    ) -> None:

        super().__init__(address, instrument_name, query_delay)

        self.cw = CW(self)
        self.sweep = Sweep(self)
