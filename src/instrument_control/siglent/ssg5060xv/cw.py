"""CW Mode Commands and Properties

This holds the basic CW functionality of the signal generator - setting power
and frequency, enabling and disabling the RF output of the instrument.
"""

from __future__ import annotations
from typing import final

from ...common.subsystem import Subsystem
from ...common.scpi_property import SCPIProperty


@final
class CW(Subsystem):
    """Inherits the `Subsystem` class to gain access to the VISA connection

    A class representation of the basic functionality of a signal generator
    that provides remote control capabilities through the use of SCPI
    commands. Individual SCPI commands are represented as class properties
    using the Python Descriptor functionality.

    Please note, this class does not do any logging on its own.

    Attributes:
    """

    frequency: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:FREQuency?",
        set_cmd=":SOURce:FREQuency {} Hz",
        cast=int,
    )

    amplitude: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:POWer:LEVel:IMMediate:AMPlitude?",
        set_cmd=":SOURce:POWer:LEVel:IMMediate:AMPlitude {} dBm",
        cast=float,
    )

    output: SCPIProperty = SCPIProperty(
        get_cmd=":OUTPut:STATe?", set_cmd=":OUTPut:STATe {}", cast=int
    )

    phase_offset: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:PHASe?", set_cmd=":SOURce:PHASe {}", cast=float
    )

    phase_reset: SCPIProperty = SCPIProperty(
        get_cmd="", set_cmd=":SOURce:PHASe:RESet", cast=None
    )
