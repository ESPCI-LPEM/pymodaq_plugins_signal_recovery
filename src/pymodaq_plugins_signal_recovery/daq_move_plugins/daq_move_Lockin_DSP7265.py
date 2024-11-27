"""
Created the 26/11/2024

@author: Louis Grandvaux
"""
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base,
    DataActuator,
    DataActuatorType,
    comon_parameters_fun,
    main
)
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.utils.parameter import Parameter

from pymeasure.instruments.signalrecovery import DSP7265
from pymeasure.adapters import VISAAdapter, PrologixAdapter

from easydict import EasyDict as edict

import pyvisa

def build_dict_from_float_list(time_constants: list[float], unit: str = "") -> dict:
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
TIME_CONSTANTS = build_dict_from_float_list(DSP7265.TIME_CONSTANTS, "s")
GAIN = list(range(0, 100, 10))

class DAQ_Move_Lockin_DSP7265(DAQ_Move_base):
    """Plugin for the Signal Recovery DSP 7265 Instrument
    """

    _controller_units = 'Hz'
    is_multiaxes = False
    _axis_names = ['OSC']
    _epsilon = 0.01
    data_actuator_type = DataActuatorType.DataActuator

    params = [
        {'title': 'Adapter', 'name': 'adapter', 'type': 'list', 'limits': list(ADAPTERS.keys())},
        {'title': 'VISA Address:', 'name': 'address', 'type': 'list', 'limits': VISA_RESOURCES},
        {'title': 'Info', 'name': 'info', 'type': 'str', 'value': '', 'readonly': True},
        {'title': 'Input mode', 'name': 'imode', 'type': 'list', 'limits': DSP7265.IMODES},
        {'title': 'Reference', 'name': 'reference', 'type': 'list', 'limits': DSP7265.REFERENCES},
        {'title': 'Voltage mode input device', 'name': 'fet', 'type': 'list', 'limits': list(FET.keys())},
        {'title': 'Input connector shield', 'name': 'shield', 'type': 'list', 'limits': list(SHIELD.keys())},
        {'title': 'Coupling', 'name': 'coupling', 'type': 'list', 'limits': list(COUPLING.keys())},
        {'title': 'Filter time constant', 'name': 'time_constant', 'type': 'list', 'limits': list(TIME_CONSTANTS.keys())},
        {'title': 'Full-scale sensitivity', 'name': 'sensitivity', 'type': 'list',
         'limits': list(build_dict_from_float_list(DSP7265.SENSITIVITIES, 'V'))},
        {'title': 'Voltage (V)', 'name': 'voltage', 'type': 'float', 'limits': [0, 5], 'value': 1e-6},
        {'title': 'Gain (dB)', 'name': 'gain', 'type': 'list', 'limits': GAIN},
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller = DSP7265
        print(self.controller.imode)

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        freq = DataActuator(data=self.controller.frequency)  # when writing your own plugin replace this line
        freq = self.get_position_with_scaling(freq)
        return freq

    def close(self):
        """Terminate the communication protocol"""
        self.controller.shutdown()

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "imode":
            self.controller.imode = param.value()
            if param.value() == DSP7265.IMODES[0]:
                self.settings.child('sensitivity').setLimits(
                   list(build_dict_from_float_list([s * DSP7265.SEN_MULTIPLIER[0]
                                                    for s in DSP7265.SENSITIVITIES],
                                                    "V"
                    ).keys())
                )
            elif param.value() == DSP7265.IMODES[1]:
               self.settings.child('sensitivity').setLimits(
                   list(build_dict_from_float_list([s * DSP7265.SEN_MULTIPLIER[1]
                                                    for s in DSP7265.SENSITIVITIES],
                                                    "A"
                    ).keys())
                )
            elif param.value() == DSP7265.IMODES[2]:
                self.settings.child('sensitivity').setLimits(
                   list(build_dict_from_float_list([s * DSP7265.SEN_MULTIPLIER[2]
                                                    for s in DSP7265.SENSITIVITIES],
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
            if self.settings.child('imode').value() == DSP7265.IMODES[0]:
               self.controller.sensitivity = build_dict_from_float_list(
                   [s * DSP7265.SEN_MULTIPLIER[0] for s in DSP7265.SENSITIVITIES],
                   "V"
                )[self.settings.child('sensitivity').value()]
            if self.settings.child('imode').value() == DSP7265.IMODES[1]:
               self.controller.sensitivity = build_dict_from_float_list(
                   [s * DSP7265.SEN_MULTIPLIER[1] for s in DSP7265.SENSITIVITIES],
                   "A"
                )[self.settings.child('sensitivity').value()]
            if self.settings.child('imode').value() == DSP7265.IMODES[2]:
               self.controller.sensitivity = build_dict_from_float_list(
                   [s * DSP7265.SEN_MULTIPLIER[2] for s in DSP7265.SENSITIVITIES],
                   "A"
                )[self.settings.child('sensitivity').value()]
        elif param.name() == "voltage":
            self.controller.voltage = param.value()
        elif param.name() == "gain":
            self.controller.gain = param.value()
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        try:
            self.status.update(edict(info="", controller=None, initialized=False))
            if self.is_master:
                adapter = ADAPTERS[self.settings.child('adapter').value()](self.settings.child('address').value())
                self.controller = DSP7265(adapter)
            else:
                if controller is None:
                    raise Exception('No controller has been defined externally while this axe is a slave one')
                else:
                    self.controller = controller

            self.status.info = self.controller.id
            self.settings.child('info').setValue(self.status.info)
            self.status.controller = controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

        info = "Whatever info you want to log"
        initialized = self.controller.a_method_or_atttribute_to_check_if_init()  # todo
        return info, initialized

    def move_abs(self, f: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """
        f = self.check_bound(f)  #if user checked bounds, the defined bounds are applied here
        f = self.set_position_with_scaling(f)
        self.controller.frequency = f.value()

        self.target_frequency = f
        self.current_frequency = self.target_frequency
        

    def move_rel(self, f: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        f = self.check_bound(self.current_frequency + f) - self.current_frequency
        self.target_frequency = f + self.current_frequency
        f = self.set_position_relative_with_scaling(f)
        self.move_abs(self.target_frequency)

    def move_home(self):
        """Call the reference method of the controller"""

        self.move_abs(DataActuator(1e3))

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""

        pass


if __name__ == '__main__':
    main(__file__, init=False)