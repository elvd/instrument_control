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
import numpy as np
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

    # INFO Moved to `shutdown`, same as with the `SignalGenerator` class
    def shutdown(self):
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
        time.sleep(self.query_delay)
        self._instr_conn.write(":CONFigure:SANalyzer")

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

    @property
    def centre_frequency(self) -> int:
        return int(
            float(
                self._instr_conn.query(
                    ":SENSe:FREQuency:CENTer?", self.query_delay
                )
            )
        )

    @centre_frequency.setter
    def centre_frequency(self, new_frequency: Union[int, float]):
        self._instr_conn.write(f":SENSe:FREQuency:CENTer {new_frequency}Hz")

        if self._op_complete():
            self.logger.info(f"Centre frequency set to {new_frequency:.3e} Hz")
        else:
            self.logger.info(
                f"Error setting centre frequency to {new_frequency:.3e} Hz"
            )

    @property
    def frequency_span(self) -> int:
        return int(
            float(
                self._instr_conn.query(
                    ":SENSe:FREQuency:SPAN?", self.query_delay
                )
            )
        )

    @frequency_span.setter
    def frequency_span(self, new_span: Union[int, float]):
        self._instr_conn.write(f":SENSe:FREQuency:SPAN {new_span}Hz")

        if self._op_complete():
            self.logger.info(f"Frequency span set to {new_span:.3e} Hz")
        else:
            self.logger.info(
                f"Error setting frequency span to {new_span:.3e} Hz"
            )

    @property
    def start_frequency(self) -> int:
        return int(
            float(
                self._instr_conn.query(
                    ":SENSe:FREQuency:STARt?", self.query_delay
                )
            )
        )

    @start_frequency.setter
    def start_frequency(self, new_frequency: Union[int, float]):
        self._instr_conn.write(f":SENSe:FREQuency:STARt {new_frequency}Hz")

        if self._op_complete():
            self.logger.info(f"Start frequency set to {new_frequency:.3e} Hz")
        else:
            self.logger.info(
                f"Error setting start frequency to {new_frequency:.3e} Hz"
            )

    @property
    def stop_frequency(self) -> int:
        return int(
            float(
                self._instr_conn.query(
                    ":SENSe:FREQuency:STOP?", self.query_delay
                )
            )
        )

    @stop_frequency.setter
    def stop_frequency(self, new_frequency: Union[int, float]):
        self._instr_conn.write(f":SENSe:FREQuency:STOP {new_frequency}Hz")

        if self._op_complete():
            self.logger.info(f"Stop frequency set to {new_frequency:.3e} Hz")
        else:
            self.logger.info(
                f"Error setting stop frequency to {new_frequency:.3e} Hz"
            )

    @property
    def sweep_points(self) -> int:
        return int(
            float(
                self._instr_conn.query(":SENSe:SWEep:POINts?", self.query_delay)
            )
        )

    @sweep_points.setter
    def sweep_points(self, npts: int):
        self._instr_conn.write(f":SENSe:SWEep:POINts {npts}")

        if self._op_complete():
            self.logger.info(f"Number of points set to {npts}")
        else:
            self.logger.info(f"Error setting number of points to {npts}")

    @property
    def vbw(self) -> int:
        return int(
            float(
                self._instr_conn.query(
                    ":SENSe:BANDwidth:VIDeo?", self.query_delay
                )
            )
        )

    @vbw.setter
    def vbw(self, new_bw: Union[int, float]):
        self._instr_conn.write(f":SENSe:BANDwidth:VIDeo {new_bw}Hz")

        if self._op_complete():
            self.logger.info(f"Video bandwidth set to {new_bw} Hz")
        else:
            self.logger.info(f"Error setting video bandwidth to {new_bw} Hz")

    @property
    def rbw(self) -> int:
        return int(
            float(
                self._instr_conn.query(
                    ":SENSe:BANDwidth:RESolution?", self.query_delay
                )
            )
        )

    @rbw.setter
    def rbw(self, new_bw: Union[int, float]):
        self._instr_conn.write(f":SENSe:BANDwidth:RESolution {new_bw}Hz")

        if self._op_complete():
            self.logger.info(f"Resolution bandwidth set to {new_bw} Hz")
        else:
            self.logger.info(
                f"Error setting resolution bandwidth to {new_bw} Hz"
            )

    @property
    def sweep_time(self) -> float:
        return float(
            self._instr_conn.query(":SENSe:SWEep:TIME?", self.query_delay)
        )

    def read_data(self, trace: int) -> np._ArrayFloat64_co:
        data = self._instr_conn.query(
            f":READ:SANalyzer{trace}?", self.query_delay
        )

        data = data.split(",")
        data = np.array(data[1::2]).astype(np.float64)

        return data

    # TODO - list of functions to implement
    # - Fetch measurements, transform into an array, save as a data file
    # - Amplitude settings - attenuation, reference levels
    # - Measurements - averaging on/off/number of averages; types of averaging
    # - Markers, including peak search
