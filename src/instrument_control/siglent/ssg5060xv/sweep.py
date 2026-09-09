"""Sweep functionality for Siglent SSG5060X-V

Implements various frequency and amplitude sweeps - list, step, linear, and
logarithmic. These are all triggered internally and there is no software sync
over the VISA connection.
"""

from __future__ import annotations

from typing import final

from ...common.subsystem import Subsystem
from ...common.scpi_property import SCPIProperty


@final
class Sweep(Subsystem):
    """Inherits the `Subsystem` class to gain access to the VISA connection

    A class representation of the sweep functionality of a signal generator
    that provides remote control capabilities through the use of SCPI
    commands. Individual SCPI commands are represented as class properties
    using the Python Descriptor functionality.

    Please note, this class does not do any logging on its own.

    Attributes:
    """

    state: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STATe?",
        set_cmd=":SOURce:SWEep:STATe {}",
        cast=str,
    )

    type: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:TYPE?", set_cmd=":SOURce:SWEep:TYPE {}", cast=str
    )

    start_freq: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:STARt:FREQuency?",
        set_cmd=":SOURce:SWEep:STEP:STARt:FREQuency {} Hz",
        cast=int,
    )

    stop_freq: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:STOP:FREQuency?",
        set_cmd=":SOURce:SWEep:STEP:STOP:FREQuency {} Hz",
        cast=int,
    )

    start_level: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:STARt:LEVel?",
        set_cmd=":SOURce:SWEep:STEP:STARt:LEVel {} dBm",
        cast=float,
    )

    stop_level: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:STOP:LEVel?",
        set_cmd=":SOURce:SWEep:STEP:STOP:LEVel {} dBm",
        cast=float,
    )

    point_dwell_time: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:DWELl?",
        set_cmd=":SOURce:SWEep:STEP:DWEll {} s",
        cast=float,
    )

    number_points: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:POINts?",
        set_cmd=":SOURce:SWEep:STEP:POINts {}",
        cast=int,
    )

    shape: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:SHAPe?",
        set_cmd=":SOURce:SWEep:STEP:SHAPe {}",
        cast=str,
    )

    direction: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:DIRect?",
        set_cmd=":SOURce:SWEep:DIRect {}",
        cast=str,
    )

    mode: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:MODE?", set_cmd=":SOURce:SWEep:MODE {}", cast=str
    )
