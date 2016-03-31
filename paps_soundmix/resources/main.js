/**
 * Created by flo on 28.06.15.
 */


(function () {
    "use strict";

    var Library = function () {
        var self = this;
        self.version = "0.1.0";
        self.name = "SoundMixPlugin";
        self.vm = null;

        /**
         * Class representing a channel
         *
         * @param {Object}  channel Data representing a channel (id, files, state, volume, group_id)
         * @constructor
         */
        function ChannelModel (channel) {
            var self = this;
            self.id = channel.id;
            self.state = ko.observable(channel.state);
            self.volume = ko.observable(channel.volume);
            self.group_selected = ko.observable(channel.group);
            self.file_selected = ko.observable(channel.files[0]);

            /**
             * Update the state value
             *
             * @param {String}          new_value   Update state to this value
             * @param {ChannelModel}    [channel]   Channel that the change occured on
             * @param {n.Event}         [event]     Click event
             */
            self.state_set = function(new_value, channel, event) {
                self.state(new_value);
            }
        }

        /**
         * ViewModel representing this plugin's data
         *
         * @param {String}  uri     Target uri for data updates
         * @param {Object}  data    Data representing plugin (files, channels, groups)
         * @constructor
         */
        function ViewModel (uri, data) {
            console.info("Creating ViewModel");
            var self = this;
            self.uri = uri;
            self.files = ko.observableArray();
            self.channels = ko.observableArray();
            self.groups = ko.observableArray();

            /**
             * Replace and update plugin data (resets all arrays before updating)
             *
             * @param {Object}  data    Data representing plugin (files, channels, groups)
             */
            self.data_replace = function (data) {
                console.debug(data);
                var key;
                var i;
                data = new Object(data);

                if ($.isEmptyObject(data)) {
                    console.warn("No new data");
                    return;
                }

                if (data.files) {
                    self.files.removeAll();
                    for (key in data.files) {
                        if (data.files.hasOwnProperty(key)) {
                            self.files.push({
                                "id": key,
                                "file": data.files[key]
                            });
                            // console.debug(self.files()[self.files().length-1]);
                        }
                    }
                }
                if (data.groups) {
                    // TODO fix updating
                    // Save old channel associations
                    var ids = {};
                    for (i=0; i < self.channels().length; i++) {
                        var it = self.channels()[i];
                        if (it.group_selected() != undefined) {
                            ids[it.group_selected().id] = it;
                        }
                    }

                    self.groups.removeAll();
                    for (i=0; i < data.groups.length; i++) {
                        key = data.groups[i];
                        if (!key.hasOwnProperty("active_definition")) {
                            key["active_definition"] = "standing"
                        }
                        if (!key.hasOwnProperty("action")) {
                            key.action = "percent"
                        }

                        self.groups.push(key);
                        if (ids.hasOwnProperty(key.id)) {
                            ids[key.id].group_selected(key);
                        }
                    }
                }
                if (data.channels) {
                    self.channels.removeAll();
                    for (key in data.channels) {
                        if (key == "count") {
                            // ignore count value (number of channels)
                            continue;
                        }
                        if (data.channels.hasOwnProperty(key)) {
                            // replace group_id with group object
                            var channel = data.channels[key];
                            channel.group = undefined;
                            for (i=0; i < self.groups().length; i++) {
                                var group = self.groups()[i];
                                if (group.id == channel.group_id) {
                                    channel.group = group;
                                    break;
                                }
                            }
                            delete channel.group_id;

                            // replace file_id with file object
                            var file = undefined;
                            if (channel.files != undefined && channel.files.length > 0) {
                                var file_id = channel.files[0];
                                for (i=0; i < self.files().length; i++) {
                                    var f = self.files()[i];
                                    if (f.id == file_id) {
                                        file = f;
                                        break;
                                    }
                                }
                            }
                            channel.files = new Array(file);
                            self.channels.push(new ChannelModel(channel));
                        }
                    }
                }
            };

            /**
             * Send data to server (Wrapper for AUSPlugin.data_set())
             *
             * @param {Object}  data    Send to server
             */
            self.data_send = function (data) {
                return AUDPlugin.data_set(self.uri, data)
            };

            /**
             * Send complete current state of plugin
             */
            self.data_send_all = function () {
                var data = {};
                var files = {};
                var channels = {};
                var groups = [];

                files = self.files_data_get();
                groups = self.groups_data_get();
                channels = self.channels_data_get()

                if (!$.isEmptyObject(files)) {
                    data.files = files;
                }
                if (!$.isEmptyObject(channels)) {
                    data.channels = channels;
                }
                if (groups.length > 0) {
                    data.groups = groups;
                }
                // console.debug(data);
                return self.data_send(data);
            };

            /**
             * Get the current files data to transmit to server
             *
             * @returns {object} Empty object
             */
            self.files_data_get = function () {
                // TODO: files: not currently changable
                return {}
            };

            self.groups_data_sync_channels = function () {
                var i;
                // unset all channel.ids
                for (i=0; i < self.groups().length; i++) {
                    self.groups()[i].channel_id = null;
                }
                for (i=0; i < self.channels().length; i++) {
                    var cm = self.channels()[i];
                    if (cm.group_selected() != null) {
                        if (cm.group_selected().channel_id != null) {
                            alert("WARNING: Channels " + cm.id + " and " + cm.group_selected().channel_id + " use the same group (only one used)")
                        }
                        cm.group_selected().channel_id = cm.id;
                        // console.debug("Setting g" + cm.group_selected().id + " to c"+cm.id);
                    }
                }
            };

            /**
             * Get the current groups data to transmit to server
             *
             * @returns {Array} Groups data
             */
            self.groups_data_get = function () {
                // TODO: groups: not currently changable
                self.groups_data_sync_channels();
                // send back unchanged
                return self.groups();
            };

            /**
             * Get the current channels data to transmit to server
             *
             * @returns {object} Channels data
             */
            self.channels_data_get = function () {
                var data = {};
                var i;

                // TODO: count (ignoring data['count'] now)

                for (i=0; i < self.channels().length; i++) {
                    var channelModel = self.channels()[i];
                    var files = [];
                    if (channelModel.file_selected() != null) {
                        // includes undefined
                        files.push(+(channelModel.file_selected().id));
                    }
                    var channel = {
                        "id": channelModel.id,
                        "files": files,
                        "state": channelModel.state(),
                        "group_id": channelModel.group_selected() != null ? channelModel.group_selected().id : null,
                        "volume": channelModel.volume()
                    };
                    data[channel.id] = channel;
                }


                return data;
            };

            self.activate = function () {
                self.data_send_all()
            };

            /**
             * Update the state value for all valid channels
             *
             * @param {String}          new_value   Update state to this value
             * @param {ViewModel}       [vm]        ViewModel that the change occured on
             * @param {n.Event}         [event]     Click event
             */
            self.channels_state_set = function (new_value, vm, event) {
                for (var i=0; i < self.channels().length; i++) {
                    var channel = self.channels()[i];
                    if (channel.file_selected() == null && new_value == "PLAY") {
                        // no file -> would not play
                        continue;
                    }
                    channel.state_set(new_value);
                }
                self.data_send_all();
            };

            self.data_replace(data);
        }

        self.createVM = function (uri, data) {
            self.vm = new ViewModel(uri, data);
        };

        /**
         * Called when all resources have been loaded
         *
         * @param {String} plugin_name Name of loaded plugin (should be equal to .name)
         * @param {String} uri   Uri to post data changes to
         * @param {object} data  Initial/setup data
         */
        self.enter = function (plugin_name, uri, data) {
            console.info(plugin_name + " is ready");
            if ($.type(data) === "string") {
                data = $.parseJSON(data);
            }

            if (self.vm == null) {
                // create model
                console.debug(plugin_name + " created");
                self.createVM(uri, data);
                ko.applyBindings(self.vm, $("#plugin_widget")[0]);
            }
            else {
                // update model
                console.debug(plugin_name + " updated");
                self.vm.data_replace(data);
            }
            // Set seats
            AUDWidget_seats.load(data);
        };

        /**
         * Called when plugin is being unloaded
         *
         * @param {String} plugin_name Name of plugin being unloaded (should be equal to .name)
         */
        self.exit = function (plugin_name) {
            console.info(plugin_name + " is being unloaded");
            ko.cleanNode($("#plugin_widget")[0]);
            self.vm = null;
            delete window.AUDPlugin_soundmix;
        };

        /**
         * Function to send data changes to active plugin
         *
         * @param {String} widget    Widget name updating
         * @param {object} data      Changed data
         * @returns {object | undefined} Value passed to AUDWidget_*
         */
        this.widgetDataSet = function (widget, data) {
            console.info(widget + " is updating data");
            //console.debug(data);
            if (widget == "AUDWidget_seats") {
                if (self.vm) {
                    self.vm.data_replace(data);
                }
            }
            else {
                console.warn("Unsupported widget " + widget);
                console.debug(data);
            }
            return;
        };

        // Return as object
        return self;
    };

    if (!window.AUDPlugin_soundmix) {
        window.AUDPlugin_soundmix = new Library();
    }

    // Plugin loaded -> register with AUDPlugin
    AUDPlugin.plugin_register(AUDPlugin_soundmix);
})();
