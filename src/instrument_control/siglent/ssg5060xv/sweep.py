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

    # TODO: Add Sweep List functionality

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

    lin_log: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:STEP:SPACe?",
        set_cmd=":SOURce:SWEep:STEP:SPACe {}",
        cast=str,
    )

    lin_step: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:FREQuency:STEP:LINear?",
        set_cmd=":SOURce:SWEep:FREQuency:STEP:LINear {} Hz",
        cast=float,
    )

    log_step: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:FREQuency:STEP:LOGarithmic?",
        set_cmd=":SOURce:SWEep:FREQuency:STEP:LOGarithmic {}",
        cast=float,
    )

    direction: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:DIRect?",
        set_cmd=":SOURce:SWEep:DIRect {}",
        cast=str,
    )

    mode: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:MODE?", set_cmd=":SOURce:SWEep:MODE {}", cast=str
    )

    single_sweep: SCPIProperty = SCPIProperty(
        get_cmd="", set_cmd=":SOURce:SWEep:EXECute", cast=None
    )

    sweep_trigger_mode: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:TRIGger:TYPE?",
        set_cmd=":SOURce:SWEep:TRIGger:TYPE {}",
        cast=str,
    )

    point_trigger_mode: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:POINt:TRIGger:TYPE?",
        set_cmd=":SOURce:SWEep:POINt:TRIGger:TYPE {}",
        cast=str,
    )

    trigger_slope: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:INPut:TRIGger:SLOPe?",
        set_cmd=":SOURce:INPut:TRIGger:SLOPe {}",
        cast=str,
    )

    current_point: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:CURRent:DATA?", set_cmd="", cast=str
    )

    current_freq: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:CURRent:FREQuency?", set_cmd="", cast=float
    )

    current_power: SCPIProperty = SCPIProperty(
        get_cmd=":SOURce:SWEep:CURRent:LEVel?", set_cmd="", cast=float
    )
