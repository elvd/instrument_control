"""SCPI Property Class - makes adding new functionality easier

Modelled after the PyMeasure approach to things, this should use Descriptors to
avoid writing lots and lots of `@property` functions and so on.
"""

from typing import final


@final
class SCPIProperty:
    def __init__(
        self,
        get_cmd: str,
        set_cmd: str,
        cast,
        description: str = "Not Documented",
    ) -> None:
        """Descriptor class to streamline and simplify adding SCPI commands

        Args:
            get_cmd: A `str` with the SCPI command to query a parameter
            set_cmd: A `str` with the SCPI command to set a parameter
            cast: A function to convert the result of `get_cmd` to a Python
                  data type
            description: A `str` with a human-friendly description of the SCPI
                         property. Should ideally contain any information on
                         allowed values for a particular property

        Raises:
            RuntimeError: If a particular SCPI property can only be set but not
                          queried or only queried but not set. Denoted by
                          having an empty string for the `get_cmd` or `set_cmd`
                          attributes.
        """
        self.get_cmd: str = get_cmd
        self.set_cmd: str = set_cmd
        self.cast = cast
        self.description: str = description
        self.name: str | None = None

    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, obj, owner):
        if self.cast:
            return self.cast(obj.query(self.get_cmd))

        raise RuntimeError("This property can only be set")

    def __set__(self, obj, value) -> bool:
        if self.set_cmd:
            return obj.write(self.set_cmd.format(value))

        raise RuntimeError("This property can only be queried")

    def __str__(self) -> str:
        return f"Property `{self.name}`. Usage information: {self.description}. SCPI commands: {self.get_cmd} and {self.set_cmd}."

    def __repr__(self) -> str:
        return f"SCPIProperty({self.name=}, {self.get_cmd=}, {self.set_cmd=}, {self.cast=}, {self.description=}, {self.name=})"
