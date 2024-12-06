"""
Created the 26/11/2024

@author: Louis Grandvaux
"""
from typing import Tuple

from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base,
    DataActuator,
    DataActuatorType,
    comon_parameters_fun,
    main
)
from pymodaq.utils.parameter import Parameter

from pymeasure.adapters import VISAAdapter, PrologixAdapter

import pyvisa

from pymodaq_plugins_signal_recovery.hardware.dsp_7265_thread_safe import DSP7265ThreadSafe


def build_dict_from_float_list(
        time_constants: list[float],
        unit: str = "") -> dict:
    d = {}
    for tc in time_constants:
        d[f"{tc:.2e} {unit}"] = tc
    return d


rm = pyvisa.ResourceManager()
VISA_RESOURCES = rm.list_resources()
ADAPTERS = dict(VISA=VISAAdapter, Prologix=PrologixAdapter)
FET = {"Bipolar": 0, "FET": 1}
SHIELD = {"Grounded": 0, "Floating": 1}
COUPLING = {"AC": 0, "DC": 1}
TIME_CONSTANTS = build_dict_from_float_list(DSP7265ThreadSafe.TIME_CONSTANTS, "s")
GAIN = list(range(0, 100, 10))


class DAQ_Move_Lockin_DSP7265(DAQ_Move_base):
    """Plugin for the Signal Recovery DSP 7265 Instrument

    Does not currently support differential measurement.
    """

    _controller_units = 'Hz'
    is_multiaxes = True
    _axis_names = ['OSC']
    _epsilon = 0.01
    data_actuator_type = DataActuatorType.DataActuator

    params = [
        {'title': 'Adapter', 'name': 'adapter', 'type': 'list',
         'limits': list(ADAPTERS.keys())},
        {'title': 'VISA Address:', 'name': 'address', 'type': 'list',
         'limits': VISA_RESOURCES},
        {'title': 'Input mode', 'name': 'imode', 'type': 'list',
         'limits': DSP7265ThreadSafe.IMODES},
        {'title': 'Reference', 'name': 'reference', 'type': 'list',
         'limits': DSP7265ThreadSafe.REFERENCES},
        {'title': 'Voltage mode input device', 'name': 'fet', 'type': 'list',
         'limits': list(FET.keys())},
        {'title': 'Input connector shield', 'name': 'shield', 'type': 'list',
         'limits': list(SHIELD.keys())},
        {'title': 'Coupling', 'name': 'coupling', 'type': 'list',
         'limits': list(COUPLING.keys())},
        {'title': 'Filter time constant', 'name': 'time_constant',
         'type': 'list', 'limits': list(TIME_CONSTANTS.keys())},
        {'title': 'Full-scale sensitivity', 'name': 'sensitivity',
         'type': 'list', 'limits':
         list(build_dict_from_float_list(DSP7265ThreadSafe.SENSITIVITIES, 'V'))},
        {'title': 'Voltage (V)', 'name': 'voltage', 'type': 'float',
         'limits': [0, 5], 'value': 1e-6},
        {'title': 'Gain (dB)', 'name': 'gain', 'type': 'list', 'limits': GAIN}
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self) -> None:
        self.controller: DSP7265ThreadSafe = None

    def get_actuator_value(self) -> DataActuator:
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The frequency obtained after scaling conversion.
        """
        freq = DataActuator(data=self.controller.frequency)
        freq = self.get_position_with_scaling(freq)
        return freq

    def close(self) -> None:
        """Terminate the communication protocol"""
        self.controller.shutdown()

    def commit_settings(self, param: Parameter) -> None:
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been
            changed by the user
        """
        if param.name() == "imode":
            self.controller.imode = param.value()
            if param.value() == DSP7265ThreadSafe.IMODES[0]:
                self.settings.child('sensitivity').setLimits(
                    list(build_dict_from_float_list(
                        [s * DSP7265ThreadSafe.SEN_MULTIPLIER[0]
                         for s in DSP7265ThreadSafe.SENSITIVITIES],
                        "V"
                    ).keys())
                )
            elif param.value() == DSP7265ThreadSafe.IMODES[1]:
                self.settings.child('sensitivity').setLimits(
                    list(build_dict_from_float_list(
                        [s * DSP7265ThreadSafe.SEN_MULTIPLIER[1]
                         for s in DSP7265ThreadSafe.SENSITIVITIES],
                        "A"
                    ).keys())
                )
            elif param.value() == DSP7265ThreadSafe.IMODES[2]:
                self.settings.child('sensitivity').setLimits(
                    list(build_dict_from_float_list(
                        [s * DSP7265ThreadSafe.SEN_MULTIPLIER[2]
                         for s in DSP7265ThreadSafe.SENSITIVITIES],
                        "A"
                    ).keys())
                )
        elif param.name() == "reference":
            self.controller.reference = param.value()
        elif param.name() == "fet":
            self.controller.fet = FET[param.value()]
        elif param.name() == "shield":
            self.controller.shield = SHIELD[param.value()]
        elif param.name() == "coupling":
            self.controller.coupling = COUPLING[param.value()]
        elif param.name() == "time_constant":
            self.controller.time_constant = TIME_CONSTANTS[param.value()]
        elif param.name() == "sensitivity":
            if self.settings.child('imode').value() == DSP7265ThreadSafe.IMODES[0]:
                self.controller.sensitivity = build_dict_from_float_list(
                    [s * DSP7265ThreadSafe.SEN_MULTIPLIER[0]
                     for s in DSP7265ThreadSafe.SENSITIVITIES],
                    "V"
                )[self.settings.child('sensitivity').value()]
            if self.settings.child('imode').value() == DSP7265ThreadSafe.IMODES[1]:
                self.controller.sensitivity = build_dict_from_float_list(
                    [s * DSP7265ThreadSafe.SEN_MULTIPLIER[1]
                     for s in DSP7265ThreadSafe.SENSITIVITIES],
                    "A"
                )[self.settings.child('sensitivity').value()]
            if self.settings.child('imode').value() == DSP7265ThreadSafe.IMODES[2]:
                self.controller.sensitivity = build_dict_from_float_list(
                    [s * DSP7265ThreadSafe.SEN_MULTIPLIER[2]
                     for s in DSP7265ThreadSafe.SENSITIVITIES],
                    "A"
                )[self.settings.child('sensitivity').value()]
        elif param.name() == "voltage":
            self.controller.voltage = param.value()
        elif param.name() == "gain":
            self.controller.gain = param.value()
        else:
            pass

    def ini_stage(self, controller: object = None) -> Tuple[str, bool]:
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one
            actuator by controller (Master case)

        Returns
        -------
        info: str
            Id of the lockin
        initialized: bool
            False if initialization failed otherwise True
        controller: object
            Controller of the daq_move
        """
        self.ini_stage_init(slave_controller=controller)

        if self.is_master:
            adapter = ADAPTERS[self.settings.child('adapter').value()](
                self.settings.child('address').value()
            )
            self.controller = DSP7265ThreadSafe(adapter)

        try:
            info = self.controller.id
            initialized = True
        except:
            info = ""
            initialized = False

        return info, initialized

    def move_abs(self, f: DataActuator) -> None:
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target value
        """
        f = self.check_bound(f)
        f = self.set_position_with_scaling(f)
        self.controller.frequency = f.value()

        self.target_value = f
        self.current_value = self.target_value

    def move_rel(self, f: DataActuator) -> None:
        """ Move the actuator to the relative target actuator value defined by
        value

        Parameters
        ----------
        value: (float) value of the relative target frequency
        """
        f = (self.check_bound(self.current_value + f)
             - self.current_value)
        self.target_value = f + self.current_value
        f = self.set_position_relative_with_scaling(f)
        self.move_abs(self.target_value)

    def move_home(self):
        """Call the reference method of the controller

        Set oscillator to 1kHz
        """
        self.move_abs(DataActuator(1e3))

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        pass


if __name__ == '__main__':
    main(__file__, init=False)
