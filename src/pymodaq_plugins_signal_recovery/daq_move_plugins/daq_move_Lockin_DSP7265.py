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

rm = pyvisa.ResourceManager()
VISA_RESOURCES = rm.list_resources()
ADAPTERS = dict(VISA=VISAAdapter, Prologix=PrologixAdapter)

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
        {'title': 'Info', 'name': 'info', 'type': 'str', 'value': '', 'readonly': True}
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller = DSP7265

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
        if param.name() == "a_parameter_you've_added_in_self.params":
           self.controller.your_method_to_apply_this_param_change()
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