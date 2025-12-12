"""Module holding Signal Generator Classes

Currently only basic functionality for Keysight Signal Generators is included
and supported. A lot of work to be done, including splitting this into base
and inherited classes.
"""

from __future__ import annotations

import math
import sys
import time
from ipaddress import ip_address
from typing import Union

import loguru
import pyvisa


class SignalGenerator:
    """Remote control of a Keysight Signal Generator using SCPI cmds.

    A class representation of a Keysight Signal Generator, that provides
    remote control capabilities through the use of SCPI commands. A connection
    is established over a GPIB or a LAN interface. Currently only very basic
    functionality is supported.

    Attributes:
        name: A `str` with a human-friendly name for the instrument, used to
              identify it in the logs.
        logger: A `loguru.Logger` object to which to save info and diagnostic
                messages.
        query_delay: A `float` with the delay, in seconds, between VISA write
                     and read operations, default value of 250 ms.
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
        visamr: pyvisa.ResourceManager,
        address: Union[str, int],
        instr_name: str = "SigGen",
        query_delay: float = 0.25,
    ):
        """Establishes a VISA connection to an instrument and presets it

        Establishes a remote connection to a Keysight Signal Generator,
        over either GPIB or LAN interface. Presets the instrument and writes
        certain details, as reported by it, to a log file. Allows programmatic
        control over CW frequency, RF output power, and modulation state.

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

        try:
            self._instr_conn = visamr.open_resource(
                instr_address, read_termination="\n", write_termination="\n"
            )
        except pyvisa.VisaIOError as error:
            self.logger.critical(f"Could not connect to {instr_name}")
            self.logger.critical(f"Error message: {error.args}")
            raise RuntimeError("Could not connect to instrument") from error
        except Exception as error:
            self.logger.critical(
                f"A different error ocurred when connecting to {instr_name}"
            )
            self.logger.critical(f"Error message: {error.args}")
            raise RuntimeError("Critical error") from error
        else:
            self.logger.info(f"Established connection to {instr_address}")

        self.query_delay = query_delay

        self.vendor: str = ""
        self.model_number: str = ""
        self.serial_number: str = ""
        self.fw_version: str = ""

        self.options_string: str = ""
        self.boards_string: str = ""

        self.phase_ref_zeroed: bool = False

        self.reset()
        self.log_details()

    def __del__(self):
        """Destructor

        Makes sure to close the VISA connection to the instrument before the
        object is deleted.
        """
        self.logger.info(f"Closing connection to {self.name}")
        response = self._instr_conn.query(
            ":DIAGnostic:INFOrmation:OTIMe?", self.query_delay
        )
        self.logger.info(f"Instrument has been on for {response} hours")

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

        self.logger.info("Instrument reset")

    def log_details(self):
        """Logs instrument-specific details

        An internal function to log an instrument's vendor, model number, and
        other relevant details.
        """
        response = self._instr_conn.query("*IDN?", self.query_delay)
        (
            self.vendor,
            self.model_number,
            self.serial_number,
            self.fw_version,
        ) = response.split(",")

        self.vendor = self.vendor.strip()
        self.model_number = self.model_number.strip()
        self.serial_number = self.serial_number.strip()
        self.fw_version = self.fw_version.strip()

        self.logger.info(f"Instrument vendor: {self.vendor}")
        self.logger.info(f"Instrument model number: {self.model_number}")
        self.logger.info(f"Instrument serial number: {self.serial_number}")
        self.logger.info(f"Instrument firmware version: {self.fw_version}")

        self.boards_string = self._instr_conn.query(
            ":DIAGnostic:INFOrmation:BOARds?", self.query_delay
        )

        boards_info = self.boards_string.split('"')[1::2]
        for board in boards_info:
            (name, part_number, serial_number, version_number, status) = (
                board.split(",")
            )
            self.logger.info(f"Board name: {name}")
            self.logger.info(f"Board part number: {part_number}")
            self.logger.info(f"Board serial number: {serial_number}")
            self.logger.info(f"Board version number: {version_number}")
            self.logger.info(f"Board status: {status}")

        self.options_string = self._instr_conn.query(
            ":DIAGnostic:INFOrmation:OPTions:DETail?", self.query_delay
        )

        options_info = self.options_string.split('"')[1::2]
        for option in options_info:
            (name, revision, dsp_version) = option.split(",")
            self.logger.info(f"Option name: {name}")
            self.logger.info(f"Option revision: {revision}")
            self.logger.info(f"DSP version: {dsp_version}")

        response = self._instr_conn.query(
            ":DIAGnostic:INFOrmation:SDATe?", self.query_delay
        )
        self.logger.info(f"Date and time stamp of firmware: {response}")

        response = self._instr_conn.query(
            ":DIAGnostic:INFOrmation:OTIMe?", self.query_delay
        )
        self.logger.info(f"Instrument has been on for {response} hours")

        if self.model_number == "E8267D":
            response = self._instr_conn.query(
                ":DIAGnostic:INFOrmation:CCOunt:ATTenuator?", self.query_delay
            )
            self.logger.info(f"Number of attenuator switches: {response}")

        response = self._instr_conn.query(
            ":DIAGnostic:INFOrmation:CCOunt:PON?", self.query_delay
        )
        self.logger.info(f"Times instrument has been turned on: {response}")

    @property
    def frequency(self) -> float:
        """Returns the CW frequency to which the Signal Generator is set

        Queries, if necessary, the CW frequency to which the Signal Generator
        is currently set, and returns it together with its unit.

        Returns:
            A `tuple` consisting of the frequency in Hz as a `float` and the
            unit used internally, as a `str`.
        """
        return float(
            self._instr_conn.query(":SOURce:FREQuency:CW?", self.query_delay)
        )

    @frequency.setter
    def frequency(self, new_freq: Union[int, float]):
        """Sets the CW frequency of the Signal Generator

        Sends the SCPI command to set a CW frequency, waits for the operation
        to complete, and confirms success.

        Notes:
            There is no bounds checking right now, nor are units different
            than Hz supported. This will change in the future.

        Args:
            new_freq: An `int` or a `float` with the new frequency.
                      The value should be in Hz.
        """
        self._instr_conn.write(f":SOURce:FREQuency:CW {new_freq}Hz")

        if self._op_complete():
            self.logger.info(f"Frequency set to {new_freq:.3e} Hz")
        else:
            self.logger.info(f"Error setting frequency to {new_freq:.3e} Hz")

    @property
    def power(self) -> float:
        """Returns the RF output power to which the Signal Generator is set

        Queries, if necessary, the RF output power to which the Signal
        Generator is currently set, and returns it together with its unit.

        Returns:
            A `tuple` consisting of the power in dBm as a `float` and the
            unit used internally, as a `str`.
        """
        return float(
            self._instr_conn.query(
                ":SOURce:POWer:LEVel:IMMediate:AMPlitude?", self.query_delay
            )
        )

    @power.setter
    def power(self, new_power: Union[int, float]):
        """Sets the RF output power of the Signal Generator

        Sends the SCPI command to set a RF output power, waits for the
        operation to complete, and confirms success.

        Notes:
            There is no bounds checking right now, nor are units different
            than dBm supported. This will change in the future.

        Args:
            new_power: An `int` or a `float` with the new RF output power.
                      The value should be in dBm.
        """
        self._instr_conn.write(
            f":SOURce:POWer:LEVel:IMMediate:AMPlitude {new_power}dBm"
        )

        if self._op_complete():
            self.logger.info(f"Output power set to {new_power} dBm")
        else:
            self.logger.info(f"Error setting output power to {new_power} dBm")

    @property
    def output(self) -> bool:
        """Returns the state of the Signal Generator's RF Output

        Queries and returns the state of the RF output. The return value of
        the query can be either "1" / "ON" or "0" / "OFF". We convert that to
        a `bool` value of `True` or `False`.

        Returns:
            A `True` / `False` boolean value
        """
        current_state = self._instr_conn.query(
            ":OUTPut:STATe?", self.query_delay
        )

        return current_state.lower() == "1" or current_state.lower() == "on"

    @output.setter
    def output(self, new_state: Union[int, str]):
        """Sets the state of the Signal Generator's RF Output

        This is the corresponding setter method which sets the new state and
        waits for the operation to complete.

        Args:
            new_state: Either an `int` or a `str` with the new state.
                       Acceptable values are 1 / "1" / "on" or 0 / "0" / "off".
                       Other values will fail silently. This is still converted
                       to a boolean value internally.
        """
        if type(new_state) not in (int, str):
            raise ValueError(
                """Acceptable values for this option are 1 / '1' / 'on' or
                0 / '0' / 'off'"""
            )

        self._instr_conn.write(f":OUTPut:STATe {new_state}")

        if self._op_complete():
            self.logger.info(f"Output enabled set to {new_state}")
        else:
            self.logger.info(f"Error setting output enabled to {new_state}")

    @property
    def mod_state(self) -> bool:
        """Returns the state of the Signal Generator's RF modulation setting

        Queries and returns the state of the RF modulation. The return value of
        the query can be either "1" / "ON" or "0" / "OFF". We convert that to
        a `bool` value of `True` or `False`.

        Returns:
            A `True` / `False` boolean value
        """
        if "UNT" not in self.options_string and self.model_number != "E8267D":
            raise RuntimeError("Functionality not available")

        current_state = self._instr_conn.query(
            ":OUTPut:MODulation:STATe?", self.query_delay
        )

        return current_state.lower() == "1" or current_state.lower() == "on"

    @mod_state.setter
    def mod_state(self, new_state: Union[int, str]):
        """Enables or disables the Signal Generator's RF modulation setting

        This is the corresponding setter method which sets the new state and
        waits for the operation to complete.

        Args:
            new_state: Either an `int` or a `str` with the new state.
                       Acceptable values are 1 / "1" / "on" or 0 / "0" / "off".
                       Other values will fail silently. This is still converted
                       to a boolean value internally.
        """
        if "UNT" not in self.options_string and self.model_number != "E8267D":
            raise RuntimeError("Functionality not available")

        if type(new_state) not in (int, str):
            raise ValueError(
                """Acceptable values for this option are 1 / '1' / 'on' or
                0 / '0' / 'off'"""
            )

        self._instr_conn.write(f":OUTPut:MODulation:STATe {new_state}")

        if self._op_complete():
            self.logger.info(f"Modulation enabled set to {new_state}")
        else:
            self.logger.info(
                f"Error setting demodulation enabled to {new_state}"
            )

    @property
    def phase_continuous(self) -> bool:
        """Phase Continuous Fine Sweep mode"""
        supported_options = ["U01", "U02", "U04", "U06"]
        if not any(
            option in self.options_string for option in supported_options
        ):
            raise RuntimeError("Functionality not available")

        current_state = self._instr_conn.query(
            ":SOURce:FREQuency:CONTinuous:MODE?", self.query_delay
        )

        return current_state.lower() == "1" or current_state.lower() == "on"

    @phase_continuous.setter
    def phase_continuous(self, new_state: Union[int, str]):
        """Sets Phase Continuous Fine Sweep Mode"""
        supported_options = ["U01", "U02", "U04", "U06"]
        if not any(
            option in self.options_string for option in supported_options
        ):
            raise RuntimeError("Functionality not available")

        if type(new_state) not in (int, str):
            raise ValueError(
                """Acceptable values for this option are 1 / '1' / 'on' or
                0 / '0' / 'off'"""
            )

        self._instr_conn.write(f":SOURce:FREQuency:CONTinuous:MODE {new_state}")

        if self._op_complete():
            self.logger.info(f"Phase Continuous Fine Sweep Mode: {new_state}")
        else:
            self.logger.info(
                f"Error setting demodulation enabled to {new_state}"
            )

    def set_phase_reference(self):
        """Set the output phase reference to zero"""
        self._instr_conn.write(":SOURce:PHASe:REFerence")

        if self._op_complete():
            self.phase_ref_zeroed = True
            self.logger.info("Output phase reference set to zero")
        else:
            self.logger.info("Error setting output phase reference to zero")

    @property
    def mod_signal_phase(self) -> float:
        """Returns current phase adjustment of a modulating signal in radians"""
        if not self.phase_ref_zeroed:
            self.set_phase_reference()

        response = self._instr_conn.query(
            ":SOURce:PHASe:ADJust?", self.query_delay
        )

        return math.degrees(float(response))

    @mod_signal_phase.setter
    def mod_signal_phase(self, new_phase: Union[int, float]):
        """Sets a new phase adjustment of a modulating signal, in degrees"""
        if not self.phase_ref_zeroed:
            self.set_phase_reference()

        self._instr_conn.write(f":SOURce:PHASe:ADJust {new_phase}DEG")

        if self._op_complete():
            self.logger.info(f"Output phase reference set to {new_phase} DEG")
        else:
            self.logger.info(
                f"Error setting phase reference to {new_phase} DEG"
            )
