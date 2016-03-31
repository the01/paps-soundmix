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
# Created: 2016-03-03 09:17

from .plugin import SoundMixPlugin


class Angel(SoundMixPlugin):
    """ Plugin for mixing sound files """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(Angel, self).__init__(settings)
        # Overwrite active definition
        # -> all people standing are in self._people_active
        self._active_definition = "standing"

    def get_info(self):
        info = super(Angel, self).get_info()
        info['description'] = "Play an orchestra with groups"
        return info

    def resource_update_list(self, reset=False):
        with self._resource_lock:
            res = super(SoundMixPlugin, self).resource_update_list(reset)

            # Remove main.html from resources
            del self._resources['main.html']
            # Remove from diff
            res = [(key, h) for (key, h) in res if key != "main.html"]
        self.debug("Resources {}".format(res))
        return res

    def do_people_seated(self):
        """
        Move all seats currently not sitting to Not Yet Placed.
        Also move all seats that are not registered (Loaded into group, but no corresponding via on_person_new

        :rtype: None
        """
        self.debug("()")
        with self._groups_lock:
            gs = self._groups

            with self._people_lock:
                for i in gs:
                    if i == 0:
                        # Skip not yet placed
                        continue
                    gp = gs[i]['people']
                    """ :type : set """
                    # Empty seats
                    rm_seats = self._people_active.intersection(gp)
                    # Unregistered seats
                    rm_seats.update(gp - self._people)
                    # Remove from group
                    gp.difference_update(rm_seats)
                    gs[0]['people'].update(rm_seats)

    def on_config(self, settings):
        self.debug("()")
        settings = dict(settings)
        super(Angel, self).on_config(settings)
        if "do" in settings:
            cmd = settings['do']
            if cmd == "people_seated":
                self.do_people_seated()

    def get_data(self):
        return super(Angel, self).get_data()

    def on_person_new(self, people):
        self.debug("People: {}".format([str(p) for p in people]))
        super(Angel, self).on_person_new(people)

    def on_person_leave(self, people):
        self.debug("People: {}".format([str(p) for p in people]))
        super(Angel, self).on_person_leave(people)

    def on_person_update(self, people):
        self.debug("People: {}".format([str(p) for p in people]))
        super(Angel, self).on_person_update(people)

    def start(self, blocking=False):
        self.debug("()")
        super(Angel, self).start(blocking)

    def stop(self):
        self.debug("()")
        super(Angel, self).stop()
        self.save_data()