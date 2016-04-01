# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2016, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.0"
__date__ = "2016-04-01"
# Created: 2016-03-03 19:50

from flotils.runable import SignalStopWrapper

from paps.si.app.sensorServer import SensorServer


class Testserver(SensorServer, SignalStopWrapper):
    pass


if __name__ == "__main__":
    import logging
    import logging.config
    from flotils.logable import default_logging_config
    logging.config.dictConfig(default_logging_config)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("twisted").setLevel(logging.INFO)

    from paps_settings import SettingsPlugin
    from paps.crowd import CrowdController
    from paps_soundmix.angel import Angel

    settings = SettingsPlugin({
        'host': "localhost",
        'port': 5000,
        'ws_path': "/ws",
        'use_debug': True,
        'controller': True
    })
    angel = Angel({
        'channels_number': 5,
        'files': [
            "data/Bell Accent.wav",
            "data/Flute Accent 1.wav",
            "data/Flute Accent 2.wav",
            "data/Groundloop.wav",
            "data/Guitar Accent.wav",
            "data/Piano Accent 1.wav",
            "data/Piano Accent 2.wav",
            "data/Piano Solo 1.wav",
            "data/String Accent.wav",
        ],
        'resource_path': "paps_soundmix/resources/",
        'data_file': "data/angel_data.json"
    })

    c = CrowdController({
        'plugins': [angel, settings]
    })

    t = Testserver({
        'multicast_bind_ip': "0.0.0.0",
        # 'listen_bind_ip': "0.0.0.0",
        'changer': c
    })
    try:
        c.start(blocking=False)
        angel._channels_files_replace(0, 0)
        angel._channels_files_replace(1, 1)
        t.start(blocking=True)
    finally:
        if t._is_running:
            t.stop()
        c.stop()
