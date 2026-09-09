"""SCPI Property Class - makes adding new functionality easier

Modelled after the PyMeasure approach to things, this should use Descriptors to
avoid writing lots and lots of `@property` functions and so on.
"""

from typing import final


@final
class SCPIProperty:
    def __init__(self, get_cmd: str, set_cmd: str, cast) -> None:
        self.get_cmd: str = get_cmd
        self.set_cmd: str = set_cmd
        self.cast = cast

    def __get__(self, obj, owner):
        if self.cast:
            return self.cast(obj.query(self.get_cmd))
        else:
            raise RuntimeError("This property can only be invoked")

    def __set__(self, obj, value):
        obj.write(self.set_cmd.format(value))
