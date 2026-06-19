"""Digital Modulation Classes

Currently only supports some of the functionality offered by Keysight Signal
Generators such as E8267D with Option 601 and/or Option 602. These are both from
the "Custom" modulation tree, particularly the "Arb Waveform Generator" and
"Real Time I/Q Baseband".

This does NOT currently support the external I/Q inputs, whether the BNC ones
or the wideband differential ones.

This does NOT currently support custom IQ files.

In terms of the SCPI command tree, it supports the :SOURce:RADio:CUSTom and
:SOURce:RADio:DMODulation:ARB ones.
"""

from __future__ import annotations

from typing import Union

from .signal_generator import SignalGenerator


class RTIQBaseband:
    def __init__(self, instrument: SignalGenerator) -> None:
        self.instrument = instrument
        self.instrument.logger.info(
            "Setting up Real-time IQ Baseband generator"
        )

    def shutdown(self):
        self.rtiqbb_state = "off"

    @property
    def rtiqbb_state(self) -> bool:
        current_state = self.instrument._instr_conn.query(
            ":SOURce:RADio:CUSTom:STATe?", self.instrument.query_delay
        )

        return current_state.lower() == "1" or current_state.lower() == "on"

    @rtiqbb_state.setter
    def rtiqbb_state(self, new_state: Union[int, str]):
        self.instrument._instr_conn.write(
            f":SOURce:RADio:CUSTom:STATe {new_state}"
        )

        if self.instrument._op_complete():
            self.instrument.logger.info(
                f"Real-time IQ Baseband generator state set to {new_state}"
            )
        else:
            self.instrument.logger.info(f"Error setting state to {new_state}")

    @property
    def filter_alpha(self) -> float:
        return float(
            self.instrument._instr_conn.query(
                ":SOURce:RADio:CUSTom:ALPHa?", self.instrument.query_delay
            )
        )

    @filter_alpha.setter
    def filter_alpha(self, new_value: float):
        self.instrument._instr_conn.write(
            f":SOURce:RADio:CUSTom:ALPHa {new_value}"
        )

        if self.instrument._op_complete():
            self.instrument.logger.info(
                f"Filter alpha value set to {new_value}"
            )
        else:
            self.instrument.logger.info(
                f"Error setting filter alpha value to {new_value}"
            )

    @property
    def data_pattern(self) -> str:
        return self.instrument._instr_conn.query(
            ":SOURce:RADio:CUSTom:DATA?", self.instrument.query_delay
        )

    @data_pattern.setter
    def data_pattern(self, pattern_id: str):
        if pattern_id not in [
            "PN9",
            "PN11",
            "PN15",
            "PN20",
            "PN23",
            "FIX4",
            "P4",
            "P8",
            "P16",
            "P32",
            "P64",
        ]:
            raise ValueError("Please pick supported data pattern")
        else:
            self.instrument._instr_conn.write(
                f":SOURce:RADio:CUSTom:DATA {pattern_id}"
            )

            if self.instrument._op_complete():
                self.instrument.logger.info(f"Data pattern set to {pattern_id}")
            else:
                self.instrument.logger.info(
                    f"Error setting data pattern to {pattern_id}"
                )

    @property
    def modulation_type(self) -> str:
        return self.instrument._instr_conn.query(
            ":SOURce:RADio:CUSTom:MODulation:TYPE?", self.instrument.query_delay
        )

    @modulation_type.setter
    def modulation_type(self, modulation: str):
        if modulation not in [
            "ASK",
            "BPSK",
            "QPSK",
            "UQPSK",
            "IS95QPSK",
            "GRAYQPSK",
            "OQPSK",
            "IS95OQPSK",
            "P4DQPSK",
            "PSK8",
            "PSK16",
            "D8PSK",
            "HDQPSK",
            "MSK",
            "FSK2",
            "FSK4",
            "FSK8",
            "FSK16",
            "C4FM",
            "HCPM",
            "QAM4",
            "QAM16",
            "QAM32",
            "QAM64",
            "QAM128",
            "APSK16CR34",
            "APSK16CR45",
            "APSK16CR56",
            "APSK16CR89",
            "APSK16CR910",
            "APSK32CR34",
            "APSK32CR45",
            "APSK32CR56",
            "APSK32CR89",
            "APSK32CR910",
        ]:
            raise ValueError("Please pick supported modulation type")
        else:
            self.instrument._instr_conn.write(
                f":SOURce:RADio:CUSTom:MODulation:TYPE {modulation}"
            )

            if self.instrument._op_complete():
                self.instrument.logger.info(f"Modulation set to {modulation}")
            else:
                self.instrument.logger.info(
                    f"Error setting modulation to {modulation}"
                )

    @property
    def symbol_rate(self) -> int:
        return int(
            float(
                self.instrument._instr_conn.query(
                    ":SOURce:RADio:CUSTom:SRATe?", self.instrument.query_delay
                )
            )
        )

    @symbol_rate.setter
    def symbol_rate(self, new_rate: Union[int, float]):
        self.instrument._instr_conn.write(
            f":SOURce:RADio:CUSTom:SRATe {new_rate}"
        )

        if self.instrument._op_complete():
            self.instrument.logger.info(f"Data rate set to {new_rate}")
        else:
            self.instrument.logger.info(
                f"Error setting data rate to {new_rate}"
            )
