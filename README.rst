pymodaq_plugins_signal_recovery
###############################

.. the following must be adapted to your developped package, links to pypi, github  description...

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_signal_recovery.svg
   :target: https://pypi.org/project/pymodaq_plugins_signal_recovery/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_signal_recovery/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_signal_recovery
   :alt: Publication Status

Set of PyMoDAQ plugins for instruments from Signal Recovery


Authors
=======

* Sebastien J. Weber  (sebastien.weber@cemes.fr)
* Louis Grandvaux (louis.grandvaux@espci.fr)


Instruments
===========

Below is the list of instruments included in this plugin

Actuators
+++++++++

* **Lockin_DSP7270**: control of the Lockin DSP7270 model (for instance to control the oscillator frequency)
* **Lockin_DSP7265**: control of the Lockin DSP7265 model (diffenrential measurement not implemented)

Viewer0D
++++++++

* **Lockin_DSP7270**: control of the Lockin DSP7270 model
* **Lockin_DSP7265**: control of the Lockin DSP7265 model



Infos
=====

Based on the *pymeasure* package providing instruments base class among which the DSP7265 and DSP7270

DSP 7265
++++++++

DSP7265 only support gpib communication protocol using NI-VISA driver.

DSP 7270
++++++++

The Signal Recovery driver *SRUSBDRIVERSV4* of the lockin should be installed for the usb connection to be recognized
by the VISA protocol.

The USB communication odf the DSP7270 should be set to *NULL*
