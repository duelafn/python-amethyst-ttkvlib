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

import amethyst_ttkvlib.behaviors.slate


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


class App(Factory.PlayerSlateBehavior, kivy.app.App):
    """
    :cvar XDG_APP: Name of your application. Is used by the `user_*()`
    methods as the app's XDG subdirectory.
    """

    def _(self, key):
        return key

    def user_conf(self, *names, **kwargs):
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

    def user_data(self, *names, **kwargs):
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

    def user_cache(self, *names, **kwargs):
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
