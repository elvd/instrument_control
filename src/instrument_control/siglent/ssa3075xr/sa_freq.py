"""Spectrum Analyser - Frequency Subsection for Siglent SSA3075X-R

This class holds the SCPI commands for setting and querying the basic frequency
related settings of the SSA3075X-R when in Spectrum Analyser (SA) mode. Some
of these will likely overlap with the Real-Time SA mode too.
"""

from __future__ import annotations
from typing import final

from ...common.subsystem import Subsystem
from ...common.scpi_property import SCPIProperty


@final
class SAFreq(Subsystem):
    """Inherits the `Subsystem` class to gain access to the VISA connection

    A class representation of the basic functionality of a signal generator
    that provides remote control capabilities through the use of SCPI
    commands. Individual SCPI commands are represented as class properties
    using the Python Descriptor functionality.

    Please note, this class does not do any logging on its own.

    Attributes:
    """

    centre: SCPIProperty = SCPIProperty(
        get_cmd=":SENSe:FREQuency:CENTer?",
        set_cmd=":SENSe:FREQuency:CENTer {} Hz",
        cast=int,
    )

    start: SCPIProperty = SCPIProperty(
        get_cmd=":SENSe:FREQuency:STARt?",
        set_cmd=":SENSe:FREQuency:STARt {} Hz",
        cast=int,
    )

    stop: SCPIProperty = SCPIProperty(
        get_cmd=":SENSe:FREQuency:STOP?",
        set_cmd=":SENSe:FREQuency:STOP {} Hz",
        cast=int,
    )

    span: SCPIProperty = SCPIProperty(
        get_cmd=":SENSe:FREQuency:SPAN?",
        set_cmd=":SENSe:FREQuency:SPAN {} Hz",
        cast=int,
    )

    zero_span: SCPIProperty = SCPIProperty(
        get_cmd="", set_cmd=":SENSe:FREQuency:SPAN:ZERO", cast=None
    )

    full_span: SCPIProperty = SCPIProperty(
        get_cmd="", set_cmd=":SENSe:FREQuency:SPAN:FULL", cast=None
    )
