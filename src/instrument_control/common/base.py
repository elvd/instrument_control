"""Basic instrument class that holds a VISA connection plus basic commands

This supports basic initialisation of the instrument, standard IEEE488.2
commands, plus wrappers for `write` and `query` methods. Inherited by specific
instrument classes which also bring together the various subsystem classes.
"""

import time
import pyvisa
from ipaddress import ip_address


class Instrument:
    def __init__(
        self,
        address: str,
        instrument_name: str = "instrument",
        query_delay: float = 0.25,
    ) -> None:
        """Establishes a VISA connection to an instrument and resets it

        Establishes a remote connection to an instrument to be controlled,
        over either GPIB or LAN interface. Resets the instrument and allows
        programmatic control over its various parameters and functionalities.

        Args:
            address: A `str` with an IPv4 address.
            instrument_name: A `str` with a a name, or alias, for the
                             instrument, to identify it more easily in the
                             logs.
            query_delay: A `float` with the delay between VISA write and
                         read operations, in seconds.
        Raises:
            ValueError: If an invalid IPv4 address is specified.
            RuntimeError: If a remote connection to the instrument cannot be
                          established.
        """
        try:
            _ = ip_address(address)
        except ValueError as error:
            raise ValueError("Please use a valid IP address") from error
        else:
            self.instrument_address: str = f"TCPIP0::{address}::inst0::INSTR"

        self._rm: pyvisa.ResourceManager = pyvisa.ResourceManager()

        try:
            self._inst = self._rm.open_resource(
                resource_name=self.instrument_address,
                read_termination="\n",
                write_termination="\n",
            )
        except pyvisa.VisaIOError as error:
            raise RuntimeError("Could not connect to instrument") from error
        except Exception as error:
            raise RuntimeError("Critical error") from error

        self.name: str = instrument_name
        self.query_delay: float = query_delay

        self.reset()

    def write(self, command: str) -> bool:
        """Wrapper around the low-level VISA `write` function

        Makes sure the operation has completed after the command has been
        sent to the instrument.
        """
        self._inst.write(command)

        time.sleep(self.query_delay)

        return self.op_complete()

    def query(self, command: str) -> str:
        """Wrapper around the low-level VISA `query` function

        Makes sure all commands are sent with appropriate `query_delay` to
        avoid any issues.
        """
        response = self._inst.query(command, self.query_delay)

        return str(response)

    def op_complete(self) -> bool:
        """Waits for operation to complete

        Queries the instrument for completion of any pending operations. The
        query should only return once everything is complete.

        Returns:
            A `True` or `False` boolean value. Should only ever return `True`.
        """
        response: str = self.query(command="*OPC?")

        return response.lower() == "1"

    def reset(self):
        """Resets an instrument to factory default settings

        Standard commands to reset an instrument to factory default settings,
        and to clear the status register of the instrument.
        """
        _ = self.write(command="*RST")
        _ = self.write(command="*CLS")
