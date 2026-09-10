"""Base Instrument Module - basic SCPI implementation

This contains a very simple class to avoid repetition of code for sending and
querying SCPI commands. The `write` and `query` methods are implemented by the
`Instrument` class and are themselves wrappers around the `PyVISA` ones.

They do include query delays and use "*OPC?" when writing commands.
"""


class Subsystem:
    def __init__(self, instrument) -> None:
        self.instrument = instrument

    def write(self, command: str) -> bool:
        return self.instrument.write(command)

    def query(self, command: str) -> str:
        return self.instrument.query(command)
