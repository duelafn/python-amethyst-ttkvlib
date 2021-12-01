# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: GPL-3.0

__all__ = '''
PlayerSlateBehavior
SlateSubwidgetBehavior
'''.split()

from amethyst.core import cached_property

from kivy.factory import Factory

from amethyst_games import NoticeType


class PlayerSlateBehavior(object):
    """
    :ivar game: Amethyst game engine.

    :ivar player_num: Player using this slate, may be None for a kibitzer.

    :ivar notice_dispatchers: Dictionary mapping amethyst game NoticeType
    to callback prefixes for automatic dispatch. See the
    `dispatch_notice()` method below for details.
    """
    game = Factory.ObjectProperty()
    player_num = Factory.NumericProperty(None, allownone=True)

    def __init__(self, *args, **kwargs):
        self.notice_dispatchers = dict()
        super().__init__(*args, **kwargs)
        for name, type in NoticeType.items():
            self.notice_dispatchers.setdefault(type, "notice_{}".format(name.lower()))

    def on_player_num(self, *args):
        self._automatic_observer()
    def on_game(self, *args):
        self._automatic_observer()

    def _automatic_observer(self):
        observer = getattr(self, '_observer', None)
        if observer:
            observer[1].unobserve(observer[0], self.dispatch_notice)
            self._observer = None
        if self.game is not None:
            self._observer = (self.player_num, self.game)
            self.game.observe(self.player_num, self.dispatch_notice)

    def dispatch_notice(self, game, seq, player_num, notice):
        """
        Dispatcher for game notices. If you set the `player_num` and `game`
        attributes, this method will be automatically attached to the game
        as an observer via:

            self.game.observe(self.player_num, self.dispatch_notice)

        Then any registered notice types will be forwarded to app methods.
        For instance, if your game has a "start_turn" action, then whenever
        the it is called, this dispatcher will call:

            self.on_notice_call_start_turn(game, player_num, notice.data):

        By default, all registered notice types will be dispatched to their
        registered identifier with a prefix of "on_notice_". Notice types
        can be added or removed from the `notice_dispatchers` attribute.
        For instance, to ignore GRANT notices:

            self.notice_dispatchers.pop(amethyst_games.notice.NoticeType.GRANT, None)

        Or to dispatch a WHISPER notice from a custom plugin (note that
        "on_" is force-prefixed),

            self.notice_dispatchers["whisper"] = "notice_whisper"
            # now whisper notices will dispatch to f"on_notice_whisper_{notice.name}"
        """
        if notice.type in self.notice_dispatchers:
            if notice.name is None:
                cb = getattr(self, f"on_{self.notice_dispatchers[notice.type]}", None)
            else:
                cb = getattr(self, f"on_{self.notice_dispatchers[notice.type]}_{notice.name}", None)
            if cb and callable(cb):
                cb(game, player_num, notice.data)



class SlateSubwidgetBehavior(object):
    """
    Behavior for a widget that expects to be contained in a player "slate".

    In a normal kivy program, the `app` kv-lang variable holds the current
    application making it a natural place to hang global callbacks and
    actions. In a multi-user game application, Each individual player's
    "slate" is often a more natural place, and actions should be called on
    whichever slate owns the subwidget.

    This behavior adds a `slate` attribute to a widget which will walk the
    parent tree and return the first slate it finds (first slate attribute
    from a parent who also implements the `SlateSubwidgetBehavior`).
    """

    def _find_slate(self):
        parent = getattr(self, 'parent', None)
        while parent is not None:
            if isinstance(parent, SlateSubwidgetBehavior):
                return getattr(parent, 'slate', None)
            parent = getattr(parent, 'parent', None)
        return None
    slate = Factory.AliasProperty(_find_slate, bind=['parent'], rebind=True, cache=True)


Factory.register("PlayerSlateBehavior", PlayerSlateBehavior)
Factory.register("SlateSubwidgetBehavior", SlateSubwidgetBehavior)
