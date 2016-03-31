(function () {
    "use strict";

    var Library = function () {
        var self = this;
        self.version = "0.1.0";
        self.name = "Angel";
        self.smpExit = null;
        self.smpEnter = null;
        self.smpCreateVM = null;

        self.doSeated = function () {
            var data = {};
            data.do = "people_seated";
            AUDPlugin_soundmix.vm.data_send(data).then(function () {
                console.debug(data);
            });
        };

        self.createVM = function (uri, data) {
            if (window.hasOwnProperty("AUDPlugin_soundmix") && AUDPlugin_soundmix_angel.smpEnter != null) {
                AUDPlugin_soundmix_angel.smpCreateVM(uri, data);
            }
            AUDPlugin_soundmix.vm.doSeated = self.doSeated;
        };

        self.enter = function (plugin_name, uri, data) {
            console.debug(self);
            if (window.hasOwnProperty("AUDPlugin_soundmix") && AUDPlugin_soundmix_angel.smpEnter != null) {
                AUDPlugin_soundmix_angel.smpEnter(plugin_name, uri, data);
            }
        };

        self.exit = function (plugin_name) {
            if (window.hasOwnProperty("AUDPlugin_soundmix") && AUDPlugin_soundmix_angel.smpExit != null) {
                AUDPlugin_soundmix.exit = AUDPlugin_soundmix_angel.smpExit;
                AUDPlugin_soundmix.exit(plugin_name);
            }
            delete window.AUDPlugin_soundmix_angel;
        };

        // Return as object
        return self;
    };

    function bootstrap () {
        if (! window.hasOwnProperty("AUDPlugin_soundmix")) {
            // Wait for AUDPlugin_soundmix to be available
            console.debug("Waiting for paps_soundmix");
            setTimeout(bootstrap, 1);
            return;
        }
        console.debug("Soundmix here");
        AUDPlugin_soundmix_angel.smpExit = AUDPlugin_soundmix.exit;
        AUDPlugin_soundmix_angel.smpEnter = AUDPlugin_soundmix.enter;
        AUDPlugin_soundmix_angel.smpCreateVM = AUDPlugin_soundmix.createVM;
        AUDPlugin_soundmix.exit = AUDPlugin_soundmix_angel.exit;
        AUDPlugin_soundmix.enter = AUDPlugin_soundmix_angel.enter;
        AUDPlugin_soundmix.createVM = AUDPlugin_soundmix_angel.createVM;
        AUDPlugin_soundmix.name = AUDPlugin_soundmix_angel.name;
    }

    if (!window.AUDPlugin_soundmix_angel) {
        window.AUDPlugin_soundmix_angel = new Library();
    }

    bootstrap();
})();

