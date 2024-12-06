"""
Created the 27/11/2024

@author: Louis Grandvaux
"""
from typing import Tuple

import pyvisa
import numpy as np

from pymeasure.adapters import VISAAdapter, PrologixAdapter

from pymodaq.control_modules.viewer_utility_classes import (
    DAQ_Viewer_base,
    comon_parameters,
    main
)
from pymodaq.utils.parameter import Parameter, utils
from pymodaq.utils.data import DataFromPlugins, DataToExport

from pyqtgraph.parametertree.Parameter import registerParameterType
from pyqtgraph.parametertree.parameterTypes.basetypes import GroupParameter

from pymodaq_plugins_signal_recovery.hardware.dsp_7265_thread_safe import DSP7265ThreadSafe

CHANNELS = ['x', 'y', 'mag', 'phase', 'adc1', 'adc2', 'adc3']
rm = pyvisa.ResourceManager()
VISA_RESOURCES = rm.list_resources()
ADAPTERS = dict(VISA=VISAAdapter, Prologix=PrologixAdapter)

for channel in CHANNELS:
    assert hasattr(DSP7265ThreadSafe, channel)


class ChannelGroup(GroupParameter):
    """Group Parameter listing the different output
    """

    def __init__(self, **opts) -> None:
        opts['type'] = 'dsp7265channel'
        opts['addText'] = "Add Channel"
        super().__init__(**opts)

    def addNew(self) -> None:
        """Add new channel to viewer
        """
        name_prefix = 'channel'

        child_indexes = [int(par.name()[len(name_prefix) + 1:])
                         for par in self.children()]

        if child_indexes == []:
            newindex = 0
        else:
            newindex = max(child_indexes) + 1

        child = {
            'title': f'Measure {newindex:02.0f}',
            'name': f'{name_prefix}{newindex:02.0f}',
            'type': 'itemselect',
            'removable': True,
            'value': dict(all_items=CHANNELS, selected=CHANNELS[0])
        }

        self.addChild(child)


registerParameterType('dsp7265channel', ChannelGroup, override=True)


class DAQ_0DViewer_Lockin_DSP7265(DAQ_Viewer_base):
    """DAQ_viewer for DSP 7265 lockin
    """

    params = [
        {'title': 'Adapter', 'name': 'adapter', 'type': 'list',
         'limits': list(ADAPTERS.keys())},
        {'title': 'VISA Address:', 'name': 'address', 'type': 'list',
         'limits': VISA_RESOURCES},
        {'title': 'ID:', 'name': 'id', 'type': 'str'},
        {'title': 'Channels:', 'name': 'channels', 'type': 'dsp7270channel'}
    ] + comon_parameters

    def ini_attributes(self) -> None:
        self.controller: DSP7265ThreadSafe = None

    def commit_settings(self, param: Parameter) -> None:
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been
            changed by the user
        """
        if param.name() in utils.iter_children(
                self.settings.child('channels'), []):
            data = []
            for child in self.settings.child('channels').children():
                labels = child.value()['selected']
                data.append(
                    DataFromPlugins(
                        name=child.name(),
                        data=[np.array([0]) for _ in labels],
                        labels=labels,
                        dim='Data0D'
                    )
                )
            self.dte_signal_temp.emit(DataToExport(
                name="lockindsp7265",
                data=data
            ))

    def ini_detector(self, controller: object = None) -> Tuple[str, bool]:
        """Viewer communication initialization

        Parameters
        ----------
        controller: (object, optional)
            custom object of a PyMoDAQ plugin (Slave case). None if only one
            actuator by controller (Master case)

        Returns
        -------
        info: str
            Id of the lockin
        initialized: bool
            False if initialization failed otherwise True
        controller: object
            Controller of the daq_viewer
        """
        self.ini_detector_init(slave_controller=controller)

        if self.is_master:
            adapter = ADAPTERS[self.settings.child('adapter').value()](
                self.settings.child('address').value()
            )
            self.controller = DSP7265ThreadSafe(adapter)

        self.dte_signal_temp.emit(
            DataToExport(
                name="lockindsp7265",
                data=[
                    DataFromPlugins(
                        name="lockindsp7265",
                        data=[np.array([0]), np.array([0])],
                        dim="Data0D",
                        labels=["x", "y"]
                    )
                ]
            )
        )

        try:
            info = self.controller.id
            initialized = True
        except:
            info = ""
            initialized = False

        return info, initialized

    def stop(self) -> None:
        return ""

    def close(self) -> None:
        pass

    def grab_data(self, Naverage: int = 1, **kwargs) -> None:
        """Grab data

        Args:
            Naverage (int, optional): Number of averaging if available.
            Defaults to 1.
        """
        data = []
        for child in self.settings.child('channels').children():
            labels = child.value()['selected'][:]
            subdata = [np.array([getattr(self.controller, label)])
                       for label in labels]
            data.append(DataFromPlugins(
                name=child.name(),
                data=subdata,
                labels=labels,
                dim='Data0D'
            ))
        self.dte_signal.emit(DataToExport(
            name="lockindsp7265",
            data=data
        ))


if __name__ == '__main__':
    main(__file__, init=False)
