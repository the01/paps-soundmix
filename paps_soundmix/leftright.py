# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2016, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.1"
__date__ = "2016-03-31"
# Created: 2016-03-02 03:24

from .plugin import SoundMixPlugin, PlayerException


class SoundMixLeftRightPlugin(SoundMixPlugin):
    """ Plugin for mixing sound files """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(SoundMixLeftRightPlugin, self).__init__(settings)

    def _volume_update(self):
        """
        Calculate percentages for each group and adjust volume
        groups_lock - people_lock - channel_lock

        :return: None
        """
        with self._groups_lock:
            gs = self._groups
            if len(gs) != 3:
                self.warning(
                    "This plugin is configured for 2 (left - right) only!!"
                )
            if len(gs) < 3:
                self.critical("Refusing to work under this conditions")
                return

            with self._people_lock:
                gl = gs.values()[1]
                """ :type : dict[unicode, int|set|unicode] """
                gr = gs.values()[2]
                """ :type : dict[unicode, int|set|unicode] """

                percent_left = self._group_calc_percentage(1, gl)
                percent_right = self._group_calc_percentage(2, gr)

                if 0.0 <= percent_left <= 1.0 and 0.0 <= percent_right <= 1.0:
                    # TODO: only update on changes
                    # Valid percentage value
                    try:
                        self._channels_volume(
                            gl['channel'], (percent_left, 0.0)
                        )
                        self._channels_volume(
                            gr['channel'], (0.0, percent_right)
                        )
                    except (ValueError, PlayerException):
                        self.exception("Failed to set volume")
