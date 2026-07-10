"""Base Instrument Class - Used to hold VISA Connection

This supports basic initialisation of any SCPI-capable instrument.
It also supports two more basic IEEE 488 commands, `*OP?` and `*RST`.
"""

from __future__ import annotations

import time
from ipaddress import ip_address

import pyvisa


class Instrument:
    """Remote control of an instrument using SCPI commands.

    A class representation of the basic functionality of an instrument that can
    be controlled with SCPI commands through a VISA connection.
    Both GPIB and LAN interfaces are supported currently.

    Please note, this class does not do any logging on its own - it raises
    errors to inform the calling module of any issues.

    Attributes:
        name: A `str` with a human-friendly name for the instrument.
        instrument_address: A `str` or an `int` with either an IPv4 or a GPIB
                            address of the instrument.
        query_delay: A `float` with the delay, in seconds, between VISA write
                     and read operations. Default value 0.25 sec.

    Methods:
        reset(): Resets the instrument to default power-on settings.
        op_complete(): Checks if all sent SCPI commands have been executed.
    """

    def __init__(
        self,
        address: str | int,
        instrument_name: str = "cw",
        query_delay: float = 0.25,
    ) -> None:
        """Establishes a VISA connection to an instrument and resets it

        Establishes a remote connection to the target instrument
        over either GPIB or LAN interface. Resets the instrument and allows
        programmatic control through further commands from other modules.

        Args:
            address: A `str` with an IPv4 address or an `int` with a GPIB
                     address. Only primary GPIB addresses, i.e. 0 - 30 are
                     supported.
            instrument_name: A `str` with a a name, or alias, for the
                             instrument, to identify it more easily in the
                             logs.
            query_delay: A `float` with the delay between VISA write and
                         read operations, in seconds.
        Raises:
            ValueError: If an invalid IPv4 or GPIB address is specified.
            RuntimeError: If a remote connection to the instrument cannot be
                          established.
        """
        if isinstance(address, str):
            try:
                _ = ip_address(address)
            except ValueError as error:
                raise ValueError("Please use a valid IP address") from error
            else:
                self.instrument_address: str = (
                    f"TCPIP0::{address}::inst0::INSTR"
                )
        else:
            if 0 <= address <= 30:
                self.instrument_address: str = f"GPIB0::{address}::INSTR"
            else:
                raise ValueError("Please use a valid GPIB address")

        self._rm: pyvisa.ResourceManager = pyvisa.ResourceManager()

        try:
            self._instr_conn = self._rm.open_resource(
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

    def op_complete(self) -> bool:
        """Waits for operation to complete

        Queries the instrument for completion of any pending operations. The
        query should only return once everything is complete.

        Returns:
            A `True` or `False` boolean value. Should only ever return `True`.
        """
        response: str = self._instr_conn.query("*OPC?", self.query_delay)

        return response.lower() == "1"

    def reset(self):
        """Resets an instrument to factory default settings

        Standard commands to reset an instrument to factory default settings,
        and to clear the status register of the instrument.
        """
        self._instr_conn.write("*RST")
        time.sleep(self.query_delay)
        self._instr_conn.write("*CLS")
        time.sleep(self.query_delay)
