import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter, utils

from pymodaq_plugins_signal_recovery.hardware.utils import get_resources
from pymeasure.instruments.ametek.ametek7270 import Ametek7270
from pyqtgraph.parametertree.Parameter import registerParameterType
from pyqtgraph.parametertree.parameterTypes.basetypes import GroupParameter


CHANNELS = ['x', 'y', 'mag', 'theta', 'adc1', 'adc2', 'adc3', 'adc4', 'x1', 'y1', 'x2', 'y2']

for channel in CHANNELS:
    assert hasattr(Ametek7270, channel)


class ChannelGroup(GroupParameter):
    """
    """

    def __init__(self, **opts):
        opts['type'] = 'dsp7270channel'
        opts['addText'] = "Add channel"
        super().__init__(**opts)

    def addNew(self):
        """

        """
        name_prefix = 'channel'

        child_indexes = [int(par.name()[len(name_prefix) + 1:]) for par in self.children()]

        if child_indexes == []:
            newindex = 0
        else:
            newindex = max(child_indexes) + 1

        child = {'title': f'Measure {newindex:02.0f}', 'name': f'{name_prefix}{newindex:02.0f}', 'type': 'itemselect',
        'removable': True, 'value': dict(all_items=CHANNELS, selected=CHANNELS[0])}

        self.addChild(child)


registerParameterType('dsp7270channel', ChannelGroup, override=True)


class DAQ_0DViewer_Lockin_DSP7270(DAQ_Viewer_base):
    """
    """
    params = comon_parameters + [
        {'title': 'Address:', 'name': 'address', 'type': 'list', 'limits': get_resources()},
        {'title': 'ID:', 'name': 'id', 'type': 'str'},
        {'title': 'Channels:', 'name': 'channels', 'type': 'dsp7270channel'}
        ]

    def ini_attributes(self):
        self.controller: Ametek7270 = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() in utils.iter_children(self.settings.child('channels'), []):
            data = []
            for child in self.settings.child('channels').children():
                labels = child.value()['selected']
                data.append(DataFromPlugins(name=child.name(), data=[np.array([0]) for _ in labels],
                                            labels=labels, dim='Data0D'))
            self.data_grabed_signal_temp.emit(data)

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        self.ini_detector_init(old_controller=controller,
                               new_controller=Ametek7270(self.settings['address']))

        info = self.controller.id
        self.settings.child('id').setValue(info)
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        self.controller.shutdown()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        data = []
        for child in self.settings.child('channels').children():
            labels = child.value()['selected'][:]
            subdata = [np.array([getattr(self.controller, label)]) for label in labels]
            data.append(DataFromPlugins(name=child.name(), data=subdata,
                                        labels=labels, dim='Data0D'))
        self.data_grabed_signal.emit(data)

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__, init=False)
