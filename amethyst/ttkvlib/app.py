# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: GPL-3.0

__all__ = '''
App
'''.split()

import os
import os.path
import pathlib

from kivy.factory import Factory
import kivy.app


def _xdg_path(env, default, app, names, file=False, mkdir=False):
    path = pathlib.Path(os.environ[env] if env in os.environ else default)
    if app is None:
        raise Exception("Error App.XDG_APP class vriable is not set to the application name.")
    if names:
        path = path.joinpath(*names)
    if mkdir:
        dir = path.parent if file else path
        dir.mkdir(parents=True, exist_ok=True)
    return pathlib.Path(path)


class App(kivy.app.App):
    """
    :cvar XDG_APP: Name of your application. Is used by the `user_*()`
    methods as the app's XDG subdirectory.

    :ivar notice_dispatchers: Dictionary mapping amethyst game NoticeType
    to callback prefixes for automatic dispatch. See the
    `dispatch_notice()` method below for details.
    """
    XDG_APP = None

    def __init__(self):
        super().__init__()
        self.notice_dispatchers = {
            "::call":      "notice_call",
            "::chat":      "notice_chat",
            "::expire":    "notice_expire",
            "::grant":     "notice_grant",
            "::init":      "notice_init",
            "::store-set": "notice_store_set",
        }


    def dispatch_notice(self, game, seq, player_num, notice):
        """
        Convenient dispatcher for game notices. If you attach this method
        as a game observer,

            game.observe(player_num, myapp.dispatch_notice)

        Then any known notice types will be forwarded to app methods. For
        instance, if your game has a "start_turn" action, then whenever the it
        is called, this dispatcher will call:

            myapp.on_notice_call_start_turn(game, player_num, notice.data):

        By default, all standard plugins in amethyst.games will be
        dispatched. Notice types can be added or removed from the
        `notice_dispatchers` attribute. For instance, to ignore GRANT
        notices:

            myapp.notice_dispatchers.pop(amethyst.games.notice.NoticeType.GRANT, None)

        Or to dispatch a WHISPER notice from a custom plugin,

            myapp.notice_dispatchers[amethyst.games.notice.NoticeType.WHISPER] = "notice_whisper"
            # now whisper notices will dispatch to f"on_notice_whisper_{notice.name}"
        """
        if notice.type in self.notice_dispatchers:
            cb = getattr(self, f"on_{self.notice_dispatchers[notice.type]}_{notice.name}", None)
            if cb and callable(cb):
                cb(game, player_num, notice.data)


    def user_conf(*names, **kwargs):
        """
        :param mkdir: When True, create the directory if it does not exist.

        :param file: When True, and mkdir is true, treat the last component
        as a file name. When False and mkdir is True, then the last path
        component is treated as a directory and will be created if missing.

        User configuration directory respecting the XDG_CONFIG_HOME
        environment variable and automatically including self.XDG_APP.

            myapp.user_conf()                                        # ~/.config/myapp
            myapp.user_conf(mkdir=True)                              # creates ~/.config/myapp
            myapp.user_conf("settings.json")                         # ~/.config/myapp/settings.json
            myapp.user_conf("settings.json", file=True, mkdir=True)  # creates ~/.config/myapp
        """
        return _xdg_path('XDG_CONFIG_HOME', os.path.expanduser("~/.config"), self.XDG_APP, names, **kwargs)

    def user_data(*names, **kwargs):
        """
        :param mkdir: When True, create the directory if it does not exist.

        :param file: When True, and mkdir is true, treat the last component
        as a file name. When False and mkdir is True, then the last path
        component is treated as a directory and will be created if missing.

        User data directory respecting the XDG_DATA_HOME environment
        variable and automatically including self.XDG_APP.

            myapp.user_data()                                        # ~/.local/share/myapp
            myapp.user_data(mkdir=True)                              # creates ~/.local/share/myapp
            myapp.user_data("state.sqlite")                          # ~/.local/share/state.sqlite
            myapp.user_data("state.sqlite", file=True, mkdir=True)   # creates ~/.local/share/myapp
        """
        return _xdg_path('XDG_DATA_HOME', os.path.expanduser("~/.local/share"), self.XDG_APP, names, **kwargs)

    def user_cache(*names, **kwargs):
        """
        :param mkdir: When True, create the directory if it does not exist.

        :param file: When True, and mkdir is true, treat the last component
        as a file name. When False and mkdir is True, then the last path
        component is treated as a directory and will be created if missing.

        User cache directory respecting the XDG_CACHE_HOME environment
        variable and automatically including self.XDG_APP.

            myapp.user_cache()                                       # ~/.cache/myapp
            myapp.user_cache(mkdir=True)                             # creates ~/.cache/myapp
            myapp.user_cache("foo.png")                              # ~/.cache/state.sqlite
            myapp.user_cache("foo.png", file=True, mkdir=True)       # creates ~/.cache/myapp
        """
        return _xdg_path('XDG_CACHE_HOME', os.path.expanduser("~/.cache"), self.XDG_APP, names, **kwargs)
