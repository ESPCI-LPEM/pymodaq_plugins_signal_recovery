import pyvisa
import numpy as np
from easydict import EasyDict as edict

from pymeasure.instruments.signalrecovery import DSP7265
from pymeasure.adapters import VISAAdapter, PrologixAdapter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter, utils
from pymodaq.utils.data import DataFromPlugins
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo

from pyqtgraph.parametertree.Parameter import registerParameterType
from pyqtgraph.parametertree.parameterTypes.basetypes import GroupParameter

CHANNELS = ['x', 'y', 'mag', 'phase', 'adc1', 'adc2', 'adc3']
rm = pyvisa.ResourceManager()
VISA_RESOURCES = rm.list_resources()
ADAPTERS = dict(VISA=VISAAdapter, Prologix=PrologixAdapter)

for channel in CHANNELS:
    assert hasattr(DSP7265, channel)

class ChannelGroup(GroupParameter):
    
    def __init__(self, **opts):
        opts['type'] = 'dsp7265channel'
        opts['addText'] = "Add Channel"
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

registerParameterType('dsp7265channel', ChannelGroup, override=True)

class DAQ_0DViewer_Lockin_DSP7265(DAQ_Viewer_base):

    params = [
        {'title': 'Adapter', 'name': 'adapter', 'type': 'list', 'limits': list(ADAPTERS.keys())},
        {'title': 'VISA Address:', 'name': 'address', 'type': 'list', 'limits': VISA_RESOURCES},
        {'title': 'ID:', 'name': 'id', 'type': 'str'},
        {'title': 'Channels:', 'name': 'channels', 'type': 'dsp7270channel'}
    ] + comon_parameters

    def ini_attributes(self):
        self.controller: DSP7265 = None

    def commit_settings(self, param: Parameter):
        if param.name() in utils.iter_children(self.settings.child('channels'), []):
            data = []
            for child in self.settings.child('channels').children():
                labels = child.value()['selected']
                data.append(DataFromPlugins(name=child.name(), data=[np.array([0]) for _ in labels],
                                            labels=labels, dim='Data0D'))
            self.data_grabed_signal_temp.emit(data)

    def ini_detector(self, controller=None):
        try:
            self.status.update(edict(info="", controller=None, initialized=False))
            if self.settings.child('controller_status').value() == "Slave":
                if controller is None:
                    raise Exception('No controller has been defined externally while this axe is a slave one')
                else:
                    print(controller)
                    self.controller = controller
            else:
                adapter = ADAPTERS[self.settings.child('adapter').value()](self.settings.child('address').value())
                self.controller = DSP7265(adapter)

            self.status.info = self.controller.id
            self.status.controller = controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def stop(self):
        return ""

    def close(self):
        pass
    
    def grab_data(self, Naverage=1, **kwargs):
        data = []
        for child in self.settings.child('channels').children():
            labels = child.value()['selected'][:]
            subdata = [np.array([getattr(self.controller, label)]) for label in labels]
            data.append(DataFromPlugins(
                name=child.name(),
                data=subdata,
                labels=labels,
                dim='Data0D'
            ))
        self.data_grabed_signal.emit(data)
    
if __name__ == '__main__':
    main(__file__, init=False)