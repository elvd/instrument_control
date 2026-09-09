What you're describing is a very common pattern in Python drivers: the **Instrument** owns the connection and exposes **subsystems** (or "facades") that encapsulate groups of SCPI commands.

Rather than having `CW` or `Sweep` inherit from `Instrument`, it's generally better for them to **hold a reference** to the instrument. This is composition rather than inheritance, and it avoids a lot of awkwardness.

## Suggested structure
```
instrument/
│
├── instrument.py      # Instrument class
├── base.py            # Shared subsystem functionality
├── cw.py              # CW subsystem
├── sweep.py           # Sweep subsystem
├── modulation.py      # Modulation subsystem
└── __init__.py
```

## Base Instrument
```python
import pyvisa

from .cw import CW
from .sweep import Sweep
from .modulation import Modulation


class Instrument:
    def __init__(self, resource_name):
        rm = pyvisa.ResourceManager()
        self._inst = rm.open_resource(resource_name)

        # expose subsystems
        self.cw = CW(self)
        self.sweep = Sweep(self)
        self.modulation = Modulation(self)

    # Low-level communication
    def write(self, cmd):
        self._inst.write(cmd)

    def query(self, cmd):
        return self._inst.query(cmd)

    # IEEE488.2 commands
    def reset(self):
        self.write("*RST")

    def opc(self):
        return self.query("*OPC?") == "1"
```

Notice that the subsystems receive `self`, not the VISA object directly. This means they can use any helper methods the instrument provides.

---

## Base subsystem class

This avoids repeating code.
```python
class Subsystem:
    def __init__(self, instrument):
        self.instrument = instrument

    def write(self, cmd):
        self.instrument.write(cmd)

    def query(self, cmd):
        return self.instrument.query(cmd)
```

Now every subsystem automatically has `write()` and `query()`.

---

## CW subsystem

```python
from .base import Subsystem

class CW(Subsystem):
    @property
    def frequency(self):
        return float(self.query("FREQ?"))

    @frequency.setter
    def frequency(self, value):
        self.write(f"FREQ {value}")
```

---

## Sweep subsystem

```python
from .base import Subsystem


class Sweep(Subsystem):
    @property
    def mode(self):
        return self.query("SWE:MODE?").strip()

    @mode.setter
    def mode(self, value):
        self.write(f"SWE:MODE {value}")
```

---

## Usage

```python
inst = Instrument("TCPIP0::192.168.0.100::INSTR")

inst.reset()

inst.cw.frequency = 10e9
print(inst.cw.frequency)

inst.sweep.mode = "LINEAR"
```

which is exactly the API you're aiming for.

---

# Why composition instead of inheritance?

It might seem tempting to write

```python
class CW(Instrument):
    ...
```

but this causes problems:

* every subsystem becomes its own `Instrument`
* each one would try to create its own VISA connection
* you'll have multiple copies of instrument state
* methods become ambiguous (`reset()` on the CW object?)

Really, there is **one instrument** with **many subsystems**.

Conceptually:
```
Instrument
│
├── VISA connection
├── reset()
├── write()
├── query()
│
├── cw
│     ├── frequency
│     └── power
│
├── sweep
│     ├── mode
│     ├── start
│     └── stop
│
└── modulation
      ├── enable
      └── source
```

This mirrors how SCPI itself is organized.

---

# Going one step further

Many professional instrument libraries (for example, QCoDeS or PyMeasure) take this idea one step further by making each SCPI parameter into a reusable descriptor.

For example:

```python
class SCPIProperty:
    def __init__(self, get_cmd, set_cmd, cast=float):
        self.get_cmd = get_cmd
        self.set_cmd = set_cmd
        self.cast = cast

    def __get__(self, obj, owner):
        return self.cast(obj.query(self.get_cmd))

    def __set__(self, obj, value):
        obj.write(self.set_cmd.format(value))
```

Then a subsystem becomes almost declarative:

```python
class CW(Subsystem):
    frequency = SCPIProperty(
        "FREQ?",
        "FREQ {}",
        float,
    )

    power = SCPIProperty(
        "POW?",
        "POW {}",
        float,
    )
```

Now adding a new SCPI parameter is just one line instead of writing separate getter and setter methods every time.

For a driver that may eventually expose dozens or hundreds of SCPI commands, this descriptor approach scales extremely well while still giving you the clean interface:

```python
inst.cw.frequency = 10e9
inst.cw.power = -10
print(inst.cw.frequency)

inst.sweep.mode = "LINEAR"
inst.modulation.enable = True
```

This combination of an `Instrument` owning a shared connection, subsystem classes using composition, and reusable property descriptors is a widely used architecture for Python instrument drivers because it keeps responsibilities well separated and remains easy to extend as the SCPI command set grows.
 
