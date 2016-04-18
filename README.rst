paps-soundmix
#############

.. image:: https://img.shields.io/pypi/v/paps-soundmix.svg
    :target: https://pypi.python.org/pypi/paps-soundmix

.. image:: https://img.shields.io/pypi/l/paps-soundmix.svg
    :target: https://pypi.python.org/pypi/paps-soundmix

.. image:: https://img.shields.io/pypi/dm/paps-soundmix.svg
    :target: https://pypi.python.org/pypi/paps-soundmix

Plugin for the `paps framework <https://pypi.python.org/pypi/paps/>`_ allowing the
user to create interactive musical performances.

At this point not available from PyPI.

SoundMixPlugin
--------------
Base plugin which uses pygame to play `.avi` files on the local machine. It provides
control methods to work with channels (add/remove files, play/pause/stop, volume control,..).
1 channel is capable of playing only a single track at the same time. However there
are at least 8 channels available for playback which means it is possible to play
8 files simultaneously.

It uses the `settings plugin <https://pypi.python.org/pypi/paps-settings>`_ to provide
a web interface to control the configuration.

You can group the available people into groups and assign tracks to these groups.
By standing up/sitting down the people are able to control the volume of their associated
tracks.

SoundMixLeftRightPlugin
-----------------------
Instead of allowing multiple groups to control their respective tracks it lets two
groups set the volume for left and right audio channel of the same track.

Angel
-----
Implements the interaction scenario described in `paps <https://github.com/the01/python-paps/blob/master/docs/index.adoc#12-initial-project-specification>`_.
It provides a slimmed down interface and functionality.

The angel_sensor_server.py in the `examples directory <https://github.com/the01/paps-soundmix/tree/master/examples>`_
demonstrates how the plugin can be used start an instance with sample files for
a simple musical performance. The code is also capable of saving and loading settings
data on start/stop (device id, group arrangements,..)

Music in `data <https://github.com/the01/paps-soundmix/tree/master/data>`_ is courtesy
of Lukas Kerck and has been made available to us under the Creative Commons Attribution
3.0 License. (`CC BY 3.0 <https://creativecommons.org/licenses/by/3.0/>`_) To view
a copy of this license, visit http://creativecommons.org/licenses/by/3.0/ or send
a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
