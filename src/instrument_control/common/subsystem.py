"""Base Instrument Module - basic SCPI implementation

This contains a very simple class to avoid repetition of code for sending and
querying SCPI commands
"""


class Subsystem:
    def __init__(self, instrument) -> None:
        self.instrument = instrument

    def write(self, command: str) -> None:
        self.instrument.write(command)

    def query(self, command: str) -> str:
        response = self.instrument.query(command, self.instrument.query_delay)
        return str(response)
