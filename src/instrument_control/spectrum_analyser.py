"""Module holding Spectrum Analyser Classes

Currently only Keysight's N9000A is included and supported. A lot of work to
be done, including splitting this into base and inherited classes.
"""

from __future__ import annotations

import sys
import time
from ipaddress import ip_address
from typing import Union

import loguru
import pyvisa


class SpectrumAnalyser:
    """Remote control of an Keysight Spectrum Analyser using SCPI commands.

    A class representation of a Keysight Spectrum Analyser, that
    provides remote control capabilities through the use of SCPI commands. A
    connection is established over a GPIB or a LAN interface. Currently only
    very basic functionality is supported.

    Attributes:
        instr_conn: A `pyvisa` object holding the remote connection to the
                    instrument. Used to send SCPI commands and read the
                    responses.
        name: A `str` with a human-friendly name for the instrument, used to
              identify it in the logs.
        logger: A `logging.Logger` object to which to save info and diagnostic
                messages.
        query_delay: A `float` with the delay, in seconds, between VISA write
                     and read operations.
        vendor: A `str` with the vendor name, as provided by the instrument
        model_number: A `str` with the model number, as provided by the
                      instrument.
        serial_number: A `str` with the serial number, as provided by the
                       instrument.
        fw_version: A `str` with the firmware version, as provided by the
                    instrument.
        details: A human-friendly `str` with a summary of the instrument's
                 self-reported details.
        frequency: A `float` or an `int` with the CW frequency of the Signal
                   Generator. Currently only supports Hz.
        power: A `float` or an `int` with the RF output power of the Signal
               Generator. Currently only supports dBm.
        output: A `bool` showing the state of the RF output of the instrument,
                i.e. ON / OFF.
        mod_state: A `bool` showing whether modulation is enabled or not.
    """

    def __init__(
        self,
        address: Union[str, int],
        instr_name: str = "SpecAn",
        query_delay: float = 0.25,
    ):
        """Establishes a VISA connection to an instrument and presets it

        Establishes a remote connection to a Keysight N9000A Spectrum Analyser,
        over either GPIB or LAN interface. Presets the instrument and writes
        certain details, as reported by it, to a log file. Allows programmatic
        control over VBW, RBW, Npts, frequency span, reading marker values.

        Args:
            visamr: A `pyvisa.ResourceManager` object used to establish a
                    remote connection to the instrument. Normally this object
                    is shared with other instruments, and is expected to be
                    initialised before the instrument.
            address: A `str` with an IPv4 address or an `int` with a GPIB
                     address. Only primary GPIB addresses, i.e. 0 - 30 are
                     supported.
            instr_name: A `str` with a a name, or alias, for the instrument,
                        to identify it more easily in the logs.
            logger: An optional `logging.Logger` object to which to write
                    diagnostic and info messages. If one is not supplied,
                    a new one is created internally.

        Raises:
            ValueError: If an invalid IPv4 or GPIB address is specified.
            RuntimeError: If a different type of address is specified, or if
                          a remote connection to the instrument cannot be
                          established.
        """
        self.name = instr_name
        self.logger = self.__get_logger()

        if isinstance(address, str):
            try:
                ip_address(address)
                instr_address = f"TCPIP0::{address}::inst0::INSTR"
            except ValueError as error:
                self.logger.warning(f"{address} is not a valid IP address")
                raise ValueError("Please use a valid IP address") from error

        elif isinstance(address, int):
            if 0 <= address <= 30:
                instr_address = f"GPIB0::{address}::INSTR"
            else:
                self.logger.warning(f"{address} is not a valid GPIB address")
                raise ValueError("Please use a valid GPIB address")
        else:
            raise RuntimeError("Only IPv4 and GPIB addresses are supported")

        self._rm = pyvisa.ResourceManager()

        try:
            self._instr_conn = self._rm.open_resource(
                instr_address, read_termination="\n", write_termination="\n"
            )
        except pyvisa.VisaIOError as error:
            self.logger.critical(f"Could not connect to {instr_name}")
            self.logger.critical(f"Error message: {error.args}")
            raise RuntimeError("Could not connect to instrument") from error
        else:
            self.logger.info(f"Established connection to {instr_address}")

        self.query_delay = query_delay

        self.vendor: str = ""
        self.model_number: str = ""
        self.serial_number: str = ""
        self.fw_version: str = ""

        self.reset()
        self.log_details()

    # WARN Does not get called when `exit()`-ing from a REPL. Context Manager?
    def __del__(self):
        """Destructor

        Makes sure to close the VISA connection to the instrument before the
        object is deleted.
        """
        self.logger.info(f"Closing connection to {self.name}")
        self._instr_conn.close()

    def __str__(self) -> str:
        """Human-friendly summary of the instrument we are connected to

        Returns a more human-friendly summary of the main details of the
        instrument to which we are connected, including the VISA address.
        """
        return (
            f"{self.vendor} {self.model_number} connected on "
            f"{self._instr_conn.resource_name} with alias {self.name}.\n"
            f"Serial number: {self.serial_number}\n"
            f"Firmware version: {self.fw_version}"
        )

    def __get_logger(self) -> loguru.Logger:
        """Sets up a `loguru.Logger` object for diagnostic and debug

        A standard function to set up and configure a `loguru.Logger` object
        for recording diagnostic and debug data.

        Args:
            None

        Returns:
            A `loguru.Logger` object with appropriate configurations. All the
            messages are duplicated to `stderr` as well.

        Raises:
            Nothing
        """
        from loguru import logger

        logger.remove()
        logger.add(
            sys.stderr,
            format=(
                "[<red>{time:YYYY-MM-DDTHH:mm:ss.SSSSSS!UTC}</red>]\t"
                "<yellow>{level}</yellow>\t"
                "<cyan>{message}</cyan>\t"
                "<white>{extra}</white>"
            ),
        )
        logger.add(
            f"{self.name}.log",
            format=(
                "[<red>{time}</red>]\t"
                "<yellow>{level}</yellow>\t"
                "<cyan>{message}</cyan>\t"
                "<white>{extra}</white>"
            ),
            rotation="100 KB",
        )

        logger.info("Logger set up")

        return logger

    def _op_complete(self) -> bool:
        """Waits for operation to complete

        Queries the instrument for completion of any pending operations. The
        query should only return once everything is complete.

        Returns:
            A `True` or `False` boolean value. Should only ever return `True`
        """

        response = self._instr_conn.query("*OPC?", self.query_delay)

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
        self._instr_conn.write(":INIT:CONT ON")

        self.logger.info("Instrument reset and initialised")

    def log_details(self):
        """Logs instrument-specific details

        An internal function to log an instrument's vendor, model number, and
        other relevant details.
        """

        idn_response = self._instr_conn.query("*IDN?", self.query_delay)
        (
            self.vendor,
            self.model_number,
            self.serial_number,
            self.fw_version,
        ) = idn_response.split(",")

        self.vendor = self.vendor.strip()
        self.model_number = self.model_number.strip()
        self.serial_number = self.serial_number.strip()
        self.fw_version = self.fw_version.strip()

        self.logger.info(f"Instrument vendor: {self.vendor}")
        self.logger.info(f"Instrument model number: {self.model_number}")
        self.logger.info(f"Instrument serial number: {self.serial_number}")
        self.logger.info(f"Instrument firmware version: {self.fw_version}")
