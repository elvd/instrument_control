"""Basic system settings for a Siglent Instrument

Implements various basic SCPI commands for setting and configuring the overall
instrument state, e.g., date, time, and so on
"""

from __future__ import annotations

from typing import final

from ...common.subsystem import Subsystem
from ...common.scpi_property import SCPIProperty


@final
class SystemSettings(Subsystem):
    """Inherits the `Subsystem` class to gain access to the VISA connection

    Please note, this class does not do any logging on its own.

    Attributes:
    """

    preset: SCPIProperty = SCPIProperty(
        get_cmd="", set_cmd=":SYSTem:PRESet", cast=None
    )

    time: SCPIProperty = SCPIProperty(
        get_cmd=":SYSTem:TIME?", set_cmd=":SYSTem:TIME {}", cast=str
    )

    date: SCPIProperty = SCPIProperty(
        get_cmd=":SYSTem:DATE?", set_cmd=":SYSTem:DATE {}", cast=str
    )

    options: SCPIProperty = SCPIProperty(
        get_cmd=":SYSTem:OPTions?", set_cmd="", cast=str
    )

    shutdown: SCPIProperty = SCPIProperty(
        get_cmd="", set_cmd=":SYSTem:POWer:OFF", cast=None
    )

    system_config: SCPIProperty = SCPIProperty(
        get_cmd=":SYSTem:CONFigure:SYSTem?", set_cmd="", cast=str
    )
