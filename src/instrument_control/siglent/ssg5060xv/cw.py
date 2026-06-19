"""Basic Signal Generator Class for Siglent SSG5060X-V

This supports basic initialisation of the instrument and setting basic
parameters such as frequency of operation and amplitude. It also supports
enabling or disabling AWGN provided it is available in the instrument.
"""

from __future__ import annotations

import time
from ipaddress import ip_address

import pyvisa


class SignalGenerator:
    """Remote control of a Siglent Signal Generator using SCPI commands.

    A class representation of the basic functionality of a signal generator
    that provides remote control capabilities through the use of SCPI
    commands. A connection over a GPIB or a LAN interface is also established
    as part of the initialisation of this class.

    Please note, this class does not do any logging on its own - it raises
    errors to inform the calling module of any issues.

    Attributes:
        name: A `str` with a human-friendly name for the instrument.
        instrument_address: A `str` or an `int` with either an IPv4 or a GPIB
                            address of the instrument.
        query_delay: A `float` with the delay, in seconds, between VISA write
                     and read operations. Default value 0.25 sec.
        frequency: A `float` or an `int` with the CW frequency of the Signal
                   Generator, in Hz.
        amplitude: A `float` or an `int` with the RF CW output power of the
                   Signal Generator, in dBm.
        output: A `bool` showing the state of the RF output of the instrument.
        phase_offset: A `float` with the phase offset of the CW signal,
                      in degrees.

    Methods:
        reset(): Resets the instrument to default power-on settings.
        op_complete(): Checks if all sent SCPI commands have been executed.
        phase_reset(): Zeroes out the phase offset of the CW signal.
    """

    def __init__(
        self,
        address: str | int,
        instrument_name: str = "cw",
        query_delay: float = 0.25,
    ) -> None:
        """Establishes a VISA connection to an instrument and resets it

        Establishes a remote connection to the Signal Generator,
        over either GPIB or LAN interface. Resets the instrument and allows
        programmatic control over CW frequency, RF output power, and
        output state.

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

    @property
    def frequency(self) -> float:
        """Returns the CW frequency to which the Signal Generator is set

        Queries the CW frequency to which the Signal Generator is currently
        set, and returns it as a float number.

        Returns:
            A `float` with the frequency in Hz.
        """
        return float(
            self._instr_conn.query(":SOURce:FREQuency?", self.query_delay)
        )

    @frequency.setter
    def frequency(self, new_freq: int | float) -> bool:
        """Sets the CW frequency of the Signal Generator

        Sends a command to set a CW frequency, waits for the operation
        to complete, and confirms success.

        Notes:
            There is no bounds checking right now, nor are units different
            than Hz supported. This might change in the future.

        Args:
            new_freq: An `int` or a `float` with the new frequency.
                      The value should be in Hz.

        Returns:
            A `bool` value to signify the command has been executed - NB,
            not the same as it being successful!
            Might get improved in the future.
        """
        self._instr_conn.write(f":SOURce:FREQuency {new_freq} Hz")

        return self.op_complete()

    @property
    def amplitude(self) -> float:
        """Returns the RF output power to which the Signal Generator is set

        Queries the RF output power to which the Signal Generator is currently
        set, and returns it as a float number.

        Returns:
            A `float` with the amplitude in dBm.
        """
        return float(
            self._instr_conn.query(
                ":SOURce:POWer:LEVel:IMMediate:AMPlitude?", self.query_delay
            )
        )

    @amplitude.setter
    def amplitude(self, new_ampl: int | float) -> bool:
        """Sets the RF output power of the Signal Generator

        Sends a command to set a particular RF output power, waits for the
        operation to complete, and confirms success.

        Notes:
            There is no bounds checking right now, nor are units different
            than dBm supported. This might change in the future.

        Args:
            new_ampl: An `int` or a `float` with the new power.
                      The value should be in dBm.

        Returns:
            A `bool` value to signify the command has been executed - NB,
            not the same as it being successful!
            Might get improved in the future.
        """
        self._instr_conn.write(
            f":SOURce:POWer:LEVel:IMMediate:AMPlitude {new_ampl} dBm"
        )

        return self.op_complete()

    @property
    def output(self) -> bool:
        """Returns the state of the Signal Generator's RF Output

        Queries and returns the state of the RF output. The return value of
        the query can be either "1" / "ON" or "0" / "OFF". We convert that to
        a `bool` value of "True" or "False".

        Returns:
            A `bool` to signify if the output is enabled.
        """
        current_state: str = self._instr_conn.query(
            ":OUTPut:STATe?", self.query_delay
        )

        return current_state.lower() == "1" or current_state.lower() == "on"

    @output.setter
    def output(self, new_state: bool) -> bool:
        """Sets the state of the Signal Generator's RF Output

        This is the corresponding setter method which sets the new state and
        waits for the operation to complete.

        Args:
            new_state: A `bool` to signify if the output should be turned on.

        Returns:
            A `bool` value to signify the command has been executed - NB,
            not the same as it being successful!
            Might get improved in the future.
        """
        if new_state:
            self._instr_conn.write(":OUTPut:STATe ON")
        else:
            self._instr_conn.write(":OUTPut:STATe OFF")

        return self.op_complete()

    @property
    def phase_offset(self) -> float:
        """Returns the value of the Signal Generator's phase offset

        Queries and returns the value of the phase offset as a `float`
        number in degrees.

        Returns:
            A `float` with the phase offset in degrees.
        """
        current_offset: str = self._instr_conn.query(
            ":SOURce:PHASe?", self.query_delay
        )

        return float(current_offset)

    @phase_offset.setter
    def phase_offset(self, new_offset: int | float) -> bool:
        """Sets the phase offset of the Signal Generator's RF CW output

        This is the corresponding setter method which changes the phase
        offset and waits for the opeartion to complete.

        Args:
            new_offset: An `int` or a `float` with the new offset in degrees.

        Returns:
            A `bool` value to signify the command has been executed - NB,
            not the same as it being successful!
            Might get improved in the future.
        """
        self._instr_conn.write(f":SOURce:PHASe {new_offset}")

        return self.op_complete()

    def phase_reset(self) -> bool:
        """Resets the phase of the CW signal

        Zeroes out the phase of the CW RF signal.

        Returns:
            A `bool` value to signify the command has been executed - NB,
            not the same as it being successful!
            Might get improved in the future.
        """
        self._instr_conn.write(":SOURce:PHASe:RESet")

        return self.op_complete()
