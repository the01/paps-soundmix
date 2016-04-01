# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.2.1"
__date__ = "2016-04-02"
# Created: 2015-07-21 18:25

import threading
from pprint import pformat

from enum import IntEnum, unique

try:
    import pygame
except ImportError:
    pygame = None

from paps.crowd import PluginException
from paps_settings import SettablePlugin


@unique
class PlayState(IntEnum):
    """ Channel State """
    STOP = 0
    """ channel stopped """
    PAUSE = 1
    """ channel paused """
    PLAY = 2
    """ channel playing """


class PlayerException(PluginException):
    """ Exception occured with player """
    pass


class SoundMixPlugin(SettablePlugin):
    """ Plugin for mixing sound files """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(SoundMixPlugin, self).__init__(settings)
        if pygame is None:
            raise PluginException("Package pygame not installed")

        self._files = {
            i: file_name
            for i, file_name in enumerate(settings['files'])
        }
        """ File id/name map
            :type : dict[int, unicode] """
        self._channels = {}
        """ Active channels
            :type _channels: dict[int, dict[unicode, object] """
        self._channels_number_default = settings.get("channels_number", 8)
        """ Number of channels per default
        (change number at runtime via _channels_number_set - method)
            :type _channels_number: int """
        self._channels_lock = threading.RLock()

        self._groups = {
            0: {
                'name': "Not yet placed people",
                'people': set(),
                'active_definition': None,
                'action': None,
                'channel': None
            }
        }
        """ Groups
            :type _groups: dict[int, dict] """
        self._groups_lock = threading.RLock()

        self._people_active = set()
        """ Set of active person ids
            :type _people_active: set[unicode] """
        self._people = set()
        """ Set of all person ids
            :type _people: set[unicode] """
        self._people_lock = threading.RLock()
        self._active_definition = settings.get('active_definition', "standing")
        if self._active_definition not in ['standing', 'sitting']:
            raise ValueError("Active definition needs to be standing/sitting")

        self._volume_should_update = threading.Event()
        """ Event signaling volume update
            :type _volume_should_update: threading.Event """
        self._updater_timeout = settings.get('updater_timeout', 1.0)
        """ Timeout for updater (merge updates) - 0.0 means no timeout
            :type _updater_timeout: float """
        self._data_file = settings.get('data_file')
        """ Location to save current settings to
            :type : None | unicode """

    def _channels_number_set(self, number):
        """
        Set the number of channels the mixer supports (Stops removed channels)

        :param number: Number of supported mixers
        :type number: int
        :rtype: None
        :raises ValueError: Number < 1
        """
        self.debug("()")
        if number <= 0:
            raise ValueError('A minimum of 1 channel is required')
        with self._channels_lock:
            cs = self._channels
            old_num = len(cs)
            if old_num == number:
                # done
                return
            if number < old_num:
                # reducing channels
                for i in range(number, old_num):
                    c = cs[i]['channel']
                    c.stop()
                    del c
                    del cs[i]
            else:
                # adding channels
                for i in range(number):
                    if i in cs:
                        continue
                    cs[i] = {
                        'channel': pygame.mixer.Channel(i),
                        'files': [],
                        'paused': False
                    }
            pygame.mixer.set_num_channels(number)

    def _channels_get(self, channel_index):
        """
        Get a channel

        Note: Assumes :attr:`channel_lock` already aquired!

        :param channel_index: Index of channel
        :type channel_index: int`
        :return: Channel with given index
        :rtype: dict
        :raises ValueError: Invalid channel index
        """
        if channel_index not in self._channels:
            raise ValueError(
                u"Channel index {} not found".format(channel_index)
            )
        return self._channels[channel_index]

    def _channels_files_replace(self, channel_index, file_index=None):
        """
        Replace files for channel

        :param channel_index: Index of channel
        :type channel_index: int
        :param file_index: Indices of file (default: None)
            (If None -> empty list)
        :type file_index: None | int | list[int]
        :rtype: None
        :raises ValueError: Invalid file index
        :raises ValueError: Invalid channel index
        """
        self.debug(u"(channel_index={}, file_index={})".format(
            channel_index, file_index
        ))
        if file_index is None:
            file_index = []
        if not isinstance(file_index, list):
            file_index = [file_index]
        for fi in file_index:
            if fi not in self._files:
                raise ValueError(u"File index {} not found".format(fi))

        with self._channels_lock:
            if channel_index not in self._channels:
                raise ValueError(
                    u"Channel index {} not found".format(channel_index)
                )
            self._channels[channel_index]['files'] = file_index

    def _channels_state_get(self, channel):
        """
        Get the current state of channel

        :param channel: Index of channel
        :type channel: int | dict
        :return: Channel state (PLAY, PAUSE, STOP)
        :rtype: PlayState
        :raises ValueError: Invalid channel index
        """
        def get_state(c):
            # assumes `get_busy` indicates playing/not playing
            if c['channel'].get_busy():
                state = PlayState.PLAY
            elif c['paused']:
                state = PlayState.PAUSE
            else:
                state = PlayState.STOP
            return state
        # self.debug("()")
        if isinstance(channel, dict):
            return get_state(channel)
        with self._channels_lock:
            if channel not in self._channels:
                raise ValueError(
                    u"Channel index {} not found".format(channel)
                )
            return get_state(self._channels[channel])

    def _channels_play(self, channel_index, file_index=None, options=None):
        """
        Play a file (and add it to channel files, if not present)

        :param channel_index: Index of channel
        :type channel_index: int
        :param file_index: Index of file (default: None)
            None -> select next from files
        :type file_index: None | int
        :param options: Additional options for playback (default: None)
        :type options: None | dict
        :rtype: None
        :raises ValueError: Invalid file index
        :raises ValueError: Invalid channel index
        :raises PlayerException: No files in channel to play
        """
        self.debug(
            u"(channel_index={}, file_index={}, options={})".format(
                channel_index, file_index, options
            )
        )
        if options is None:
            options = {}
        if file_index is not None:
            self._channels_files_replace(channel_index, file_index)

        with self._channels_lock:
            if channel_index not in self._channels:
                raise ValueError(
                    u"Channel index {} not found".format(channel_index)
                )
            c = self._channels[channel_index]
            # TODO: Maybe unpause?

            if not c['files']:
                raise PlayerException("Nothing to play")
            file_index = c['files'][0]

            try:
                sound = pygame.mixer.Sound(self._files[file_index])
            except:
                raise ValueError(
                    u"Loading sound from  '{}' failed".format(
                        self._files[file_index]
                    )
                )
            try:
                # on failure propably not paused either
                c['paused'] = False
                c['channel'].play(
                    sound,
                    options.get('loops', 0),
                    options.get('maxtime', 0),
                    options.get('fade_ms', 0)
                )
            except:
                raise PlayerException("Playing failed")

    def _channels_stop(self, channel_index):
        """
        Stop channel

        :param channel_index: Index of channel
        :type channel_index: int
        :rtype: None
        :raises ValueError: Invalid channel index
        :raises PlayerException: Error stopping
        """
        self.debug(u"(channel_index={})".format(channel_index))
        with self._channels_lock:
            if channel_index not in self._channels:
                raise ValueError(
                    u"Channel index {} not found".format(channel_index)
                )
            c = self._channels[channel_index]
            try:
                # on failure propably not paused either
                c['paused'] = False
                c['channel'].stop()
            except:
                raise PlayerException("Stopping failed")

    def _channels_pause(self, channel_index):
        """
        Pause channel

        :param channel_index: Index of channel
        :type channel_index: int
        :rtype: None
        :raises ValueError: Invalid channel index
        :raises PlayerException: Error pausing
        """
        self.debug(u"(channel_index={})".format(channel_index))
        with self._channels_lock:
            if channel_index not in self._channels:
                raise ValueError(
                    u"Channel index {} not found".format(channel_index)
                )
            c = self._channels[channel_index]
            try:
                c['channel'].pause()
            except:
                raise PlayerException("Pausing failed")
            else:
                c['paused'] = True

    def _channels_unpause(self, channel_index):
        """
        Unpause channel

        :param channel_index: Index of channel
        :type channel_index: int
        :rtype: None
        :raises ValueError: Invalid channel index
        :raises PlayerException: Error unpausing
        """
        self.debug(u"(channel_index={})".format(channel_index))
        with self._channels_lock:
            if channel_index not in self._channels:
                raise ValueError(
                    u"Channel index {} not found".format(channel_index)
                )
            c = self._channels[channel_index]
            try:
                # on failure propably not paused either
                c['paused'] = False
                c['channel'].unpause()
            except:
                raise PlayerException("Unpausing failed")

    def _channels_volume(self, channel_index, volume):
        """
        Set volume for channel

        :param channel_index: Index of channel
        :type channel_index: int
        :param volume: Volume to set - stereo or (left, right)
        :type volume: float | (float, None) | (float, float)
        :rtype: None
        :raises ValueError: Invalid channel index
        :raises PlayerException: Error setting volume
        """
        if not isinstance(volume, float) and len(volume) == 2:
            left, right = volume
        else:
            left, right = volume, volume
        # self.debug(u"Setting {} to {}-{}".format(channel_index, left, right))

        with self._channels_lock:
            if channel_index not in self._channels:
                raise ValueError(
                    u"Channel index {} not found".format(channel_index)
                )
            try:
                self._channels[channel_index]['channel'].set_volume(
                    left, right
                )
            except:
                self.exception(
                    u"Failed to change volume to {}-{}".format(left, right)
                )
                raise PlayerException("Setting volume failed")

    def _channels_do(self, channel_index, cmd, val, options=None):
        """
        Execute command on channels

        :param channel_index: Index of channel
        :type channel_index: int
        :param cmd: Command to execute (files, state, volume)
        :type cmd: unicode
        :param val: Value for command
        :type val: None | unicode | float | int | list[int]
        :param options: Additional options for command (default: {})
        :type options: dict
        :return: None
        """
        self.debug("()")
        # TODO: work over
        if options is None:
            options = {}
        if cmd == "files":
            try:
                self._channels_files_replace(channel_index, val)
            except ValueError:
                self.exception("Failed to put file")
        elif cmd == "state":
            if val == "play":
                try:
                    self._channels_play(
                        channel_index, options.get('file', None), options
                    )
                except (ValueError, PlayerException):
                    self.exception("Failed to play")
            elif val == "stop":
                try:
                    self._channels_stop(channel_index)
                except (ValueError, PlayerException):
                    self.exception("Failed to stop")
            elif val == "pause":
                try:
                    self._channels_pause(channel_index)
                except (ValueError, PlayerException):
                    self.exception("Failed to pause")
            elif val == "unpause":
                try:
                    self._channels_unpause(channel_index)
                except (ValueError, PlayerException):
                    self.exception("Failed to unpause")
        elif cmd == "volume":
            try:
                self._channels_volume(channel_index, val)
            except (ValueError, PlayerException):
                self.exception("Failed to set volume")

    def _channels_settings(self, cs_sett):
        """
        Apply channels settings

        :param cs_sett: Settings
        :type cs_sett: dict
        :rtype: None
        """
        # self.debug("()")
        with self._channels_lock:
            if "count" in cs_sett:
                try:
                    self._channels_number_set(cs_sett['count'])
                except ValueError:
                    self.exception("Failed to set channel number")
                del cs_sett['count']
            for index in cs_sett:
                c_sett = cs_sett[index]
                c = self._channels_get(c_sett['id'])
                if "files" in c_sett:
                    old = c['files']
                    if old != c_sett['files']:
                        self._channels_do(
                            c_sett['id'], "files", c_sett['files']
                        )
                if "state" in c_sett:
                    old = self._channels_state_get(c).name
                    # check if changed
                    if old != c_sett['state']:
                        if old == "PAUSE" and c_sett['state'] == "PLAY":
                            # necessary??
                            self._channels_do(c_sett['id'], "state", "unpause")
                        else:
                            self._channels_do(
                                c_sett['id'], "state", c_sett['state'].lower()
                            )
                if "volume" in c_sett:
                    old = c['channel'].get_volume()
                    if old != c_sett['volume']:
                        self._channels_do(
                            c_sett['id'], "volume", c_sett['volume']
                        )
                if "group_id" in c_sett:
                    pass
                    # old = c['group_id']
                    # avoid setting group id here, bc it would require
                    # groups_lock --> possible dead lock
                    # TODO: check dead locks -> do this on client for now
                continue
                # TODO: set group channel
                # (associtated group id here and not in group)
                for cmd in cs_sett[index]:
                    if len(cs_sett[index][cmd]) == 2:
                        val, options = cs_sett[index][cmd]
                    else:
                        val = cs_sett[index][cmd]
                        options = {}
                    self._channels_do(cmd, val, options)

    def _groups_set(self, g_sett):
        # self.debug("()")
        with self._groups_lock:
            gs = self._groups
            group_id = g_sett.get('id')
            if group_id is None or group_id not in gs:
                # generate new group (id)
                group_id = max(gs.keys()) + 1
            g = gs.setdefault(group_id, {})
            # name of group (displayed)
            g['name'] = g_sett['name']
            # people in group (set of ids)
            g['people'] = {p['id'] for p in g_sett['people']}
            # what counts as 'active' (standing/sitting)
            g['active_definition'] = g_sett['active_definition']
            # what action to take (perc/perc_total)
            g['action'] = g_sett['action']
            # corresponding channel id (set for this group) - None if nothing
            g['channel'] = g_sett['channel_id']

    def _groups_settings(self, gs_sett):
        """
        Apply groups settings

        :param gs_sett: Settings
        :type gs_sett: list[dict]
        :rtype:
        """
        # self.debug("()")
        for group in gs_sett:
            try:
                self._groups_set(group)
            except:
                self.exception("Failed to set group")

    def _group_calc_percentage(self, group_id, group):
        """
        Calculate percent of sound volume for group

        :param group_id: int
        :param group: dict[unicode, int|set|unicode]
        :return: Sound percent of group (-1.0 on failure, else 0 <= percent <= 1.0)
        :rtype: float
        """
        # Calculate percentage
        percent = -1.0
        gp = self._people.intersection(group['people'])
        """ :type : set[unicode] """
        # Assert isinstance(gp, set)
        act = self._people_active.intersection(gp)
        """ :type : set[unicode] """

        if self._active_definition != group['active_definition']:
            act = gp.difference(act)

        # self.debug(u"GP: {}".format(gp))
        # self.debug(u"Act: {}".format(act))
        action = group['action']
        if action == "percent":
            # protect div 0
            if len(gp):
                # get percentage of active people in this group
                percent = len(act) / len(gp)
        elif action == "percent_total":
            # protect div 0
            if len(self._people):
                # get percentage of active people in audience
                percent = len(act) / len(self._people)
        else:
            self.error(u"Unknown action in group {}: '{}'".format(
                group_id, action
            ))
        return percent

    def _volume_update(self):
        """
        Calculate percentages for each group and adjust volume
        groups_lock - people_lock - channel_lock

        :return: None
        """
        with self._groups_lock:
            gs = self._groups

            with self._people_lock:
                for group_id in gs:
                    # self.debug("G: {}".format(group_id))
                    g = gs[group_id]
                    """ :type : dict[unicode, int|set|unicode] """
                    if group_id == 0:
                        # don't calc for not placed group
                        continue

                    percent = self._group_calc_percentage(group_id, g)
                    # self.debug("Perc: {}".format(percent))
                    if 0.0 <= percent <= 1.0:
                        # TODO: only update on changes
                        # valid percentage value
                        try:
                            self._channels_volume(g['channel'], percent)
                        except (ValueError, PlayerException):
                            self.exception("Failed to set volume")

    def on_config(self, settings):
        self.debug("()")
        settings = dict(settings)
        self.debug(pformat(settings))

        if "channels" in settings:
            cs_sett = dict(settings['channels'])
            self._channels_settings(cs_sett)
        if "groups" in settings:
            gs_sett = list(settings['groups'])
            self._groups_settings(gs_sett)

    def get_data(self):
        with self._channels_lock:
            cs = self._channels
            channels_info = {
                'count': pygame.mixer.get_num_channels()
            }
            for i in cs:
                c = cs[i]
                ci = c['channel']
                state = self._channels_state_get(c)

                channels_info[i] = {
                    'id': i,
                    'files': c['files'],
                    'volume': ci.get_volume(),
                    'state': state.name,
                    'group_id': None
                }
        with self._groups_lock:
            group_info = []
            for group_id in self._groups:
                group = self._groups[group_id]
                g = {
                    'id': group_id,
                    'name': group['name'],
                    # json cant handle sets
                    # TODO: make json set serializer
                    'people': [{'id': p} for p in group['people']],
                    'active_definition': group['active_definition'],
                    'action': group['action'],
                    'channel_id': group['channel']
                }
                if group['channel'] is not None:
                    channels_info[group['channel']]['group_id'] = group_id
                group_info.append(g)
        self.debug(u"Result:\n{}".format(pformat({
            'channels': channels_info,
            'files': self._files,
            'groups': group_info
        })))
        return {
            'channels': channels_info,
            'files': self._files,
            'groups': group_info
        }

    def save_data(self):
        """
        Save data to file

        :rtype: None
        """
        if self._data_file:
            try:
                self._saveJSONFile(self._data_file, self.get_data())
            except:
                self.exception("Failed to save data")

    def load_data(self):
        """
        Load data from file and trigger on_config

        :rtype: None
        """
        if self._data_file:
            try:
                self.on_config(self._loadJSONFile(self._data_file))
            except:
                self.exception("Failed to load and apply data")

    def _people_is_active(self, person, active_definition=None):
        """
        Determine if this person is globally active (standing)

        :param person: Person to test
        :type person: paps.person.Person
        :param active_definition: What to consider as 'active' (default: None)
            None -> use global active definition
        :type active_definition: None | unicode
        :return: Is active
        :rtype: bool
        """
        if active_definition is None:
            active_definition = self._active_definition
        if active_definition == "standing":
            return not person.sitting
        else:
            return person.sitting

    def on_person_new(self, people):
        self.debug("People: {}".format([unicode(p) for p in people]))
        people_set = {person.id for person in people}
        with self._people_lock:
            self._people.update(people_set)
            self._people_active.update(
                {
                    person.id for person in people
                    if self._people_is_active(person)
                }
            )
            # self.debug("All: {}".format(self._people))
            # self.debug("Active: {}".format(self._people_active))
        with self._groups_lock:
            self._groups[0]['people'].update(people_set)
        # New people -> percent changed -> update
        self._volume_should_update.set()

    def on_person_leave(self, people):
        with self._people_lock:
            ps = {person.id for person in people}
            self._people -= ps
            self._people_active -= ps
            # self.debug("All: {}".format(self._people))
            # self.debug("Active: {}".format(self._people_active))
        # people left -> percent changed -> update
        self._volume_should_update.set()

    def on_person_update(self, people):
        self.debug("People: {}".format([unicode(p) for p in people]))
        with self._people_lock:
            active = {
                person.id for person in people
                if self._people_is_active(person)
            }
            inactive = {
                person.id for person in people
                if not self._people_is_active(person)
            }
            # Remove inactive
            self._people_active -= inactive
            # Add active
            self._people_active.update(active)
        # People changed -> percent changed -> update
        self._volume_should_update.set()

    def _volume_updater(self):
        """
        Threaded function responsible for timing the volume updates

        :rtype: None
        """
        while self._is_running:
            #if self._updater_timeout > 0.0:
            #    time.sleep(self._updater_timeout)
            try:
                # do it before updating -> might get triggered again
                # too often better than missed update
                self._volume_should_update.clear()
                self._volume_update()
                self._volume_should_update.wait(self._updater_timeout)
            except:
                self.exception("Updating failed")
        self.debug("ended")

    def resource_update_list(self, reset=False):
        with self._resource_lock:
            res = super(SoundMixPlugin, self).resource_update_list(reset)

            # Remove angel.html from resources
            del self._resources['angel.html']
            # Remove from diff
            res = [(key, h) for (key, h) in res if key not in ["angel.html", "angel.js"]]
            return res

    def start(self, blocking=False):
        self.debug("()")
        super(SoundMixPlugin, self).start(False)
        try:
            pygame.init()
            pygame.mixer.init()
            with self._channels_lock:
                self._channels_number_set(self._channels_number_default)
        except:
            self.exception("Failed to init mixer")
            self.stop()
            return
        # Needs pygame set up
        self.load_data()
        try:
            a_thread = threading.Thread(
                target=self._volume_updater
            )
            # Just in case
            a_thread.daemon = True
            a_thread.start()
        except:
            self.exception("Failed to start volume updater")
            self.stop()
            return
        super(SoundMixPlugin, self).start(blocking)

    def stop(self):
        self.debug("()")
        if not self._is_running:
            return
        super(SoundMixPlugin, self).stop()
        self._volume_should_update.set()
        try:
            pygame.mixer.quit()
        except:
            self.exception("Failed to stop mixer")
