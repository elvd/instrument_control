"""Basic Signal Generator Class for Siglent SSG5060X-V

This supports basic initialisation of the instrument and setting basic
parameters such as frequency of operation and amplitude. It also supports
enabling or disabling AWGN provided it is available in the instrument.
"""

from __future__ import annotations

import math
import sys
import time
from ipaddress import ip_address
from typing import Union

from numpy import true_divide
import pyvisa


class SignalGenerator:
    def __init__(
        self,
        address: str | int,
        instrument_name: str = "cw",
        query_delay: float = 0.25,
    ) -> None:
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
            A `True` or `False` boolean value. Should only ever return `True`
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
        return float(
            self._instr_conn.query(":SOURce:FREQuency?", self.query_delay)
        )

    @frequency.setter
    def frequency(self, new_freq: int | float) -> bool:
        self._instr_conn.write(f":SOURce:FREQuency {new_freq} Hz")

        return self.op_complete()

    @property
    def amplitude(self) -> float:
        return float(
            self._instr_conn.query(
                ":SOURce:POWer:LEVel:IMMediate:AMPlitude?", self.query_delay
            )
        )

    @amplitude.setter
    def amplitude(self, new_ampl: int | float) -> bool:
        self._instr_conn.write(
            f":SOURce:POWer:LEVel:IMMediate:AMPlitude {new_ampl} dBm"
        )

        return self.op_complete()

    @property
    def output(self) -> bool:
        current_state: str = self._instr_conn.query(
            ":OUTPut:STATe?", self.query_delay
        )

        return current_state.lower() == "1" or current_state.lower() == "on"

    @output.setter
    def output(self, new_state: int | str) -> bool:
        self._instr_conn.write(f":OUTPut:STATe {new_state}")

        return self.op_complete()

    @property
    def phase_offset(self) -> float:
        current_offset: str = self._instr_conn.query(
            ":SOURce:PHASe?", self.query_delay
        )

        return float(current_offset)

    @phase_offset.setter
    def phase_offset(self, new_offset: int | float) -> bool:
        self._instr_conn.write(f":SOURce:PHASe {new_offset}")

        return self.op_complete()

    def phase_reset(self) -> bool:
        self._instr_conn.write(":SOURce:PHASe:RESet")

        return self.op_complete()
