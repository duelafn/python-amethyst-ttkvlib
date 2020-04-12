# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: GPL-3.0
__all__ = '''
CardFan
CardImage
ICardFanReset
'''.split()

import math
from math import pi, radians, degrees, hypot
pi_2 = pi/2

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import inch
from kivy.clock import Clock

from amethyst.core import Object, Attr

from amethyst.games.filters import IFilterable

from amethyst.ttkvlib.util import rotation_for_animation


Builder.load_string('''
<CardImage>:
    do_rotation: False
    do_scale: False
    do_translation: False
    Image:
        id: img
        size: root.size
        source: (root.source if root.show_front else root.back_source) or ''

<CardFan>:
''')


NOVALUE = object()

def ci_getter(attr):
    def func(self):
        val = getattr(self, f"_{attr}", NOVALUE)
        if val is NOVALUE:
            return getattr(getattr(self, 'card', None), attr, None)
        return val
    func.__name__ = attr
    return func

def ci_setter(attr):
    def func(self, val):
        _val = getattr(self, f"_{attr}", NOVALUE)
        if _val != val:
            setattr(self, f"_{attr}", val)
            return True
        return False
    func.__name__ = attr
    return func


class ICardFanReset(object):
    """
    Interface indicating to a CardFan widget that a class should have its
    `.clear()` method called whenever the widget is recycled.
    """
    def clear(self):
        pass


class RevisionTracking(object):
    def _get_revision(self):
        return getattr(self, "_revision", 0)
    def _set_revision(self, val):  # value is ignored!
        self._revision = 1 + getattr(self, "_revision", 0)
        return True
    revision = Factory.AliasProperty(_get_revision, _set_revision)
    def trigger_refresh(self):
        self.revision = 1


class CardImage(ICardFanReset, IFilterable, RevisionTracking, Factory.Scatter):
    """
    A Scatter containing an Image appropriate for using as a widget in a
    CardFan.

    :ivar card: Optional arbitrary card object. If present, some other
    attributes will delegate their values (read-only) to this object.

    :ivar id: Stable identifier used by the CardFan when rearranging cards.
    If left unset, this attribute will delegate (read-only) to `card.id`
    (or None).

    :ivar source: Image source for front of card. If left unset, this
    attribute will delegate (read-only) to `card.source` (or None).

    :ivar back_source: Image source for back of card. If left unset, this
    attribute will delegate (read-only) to `card.back_source` (or None).

    :ivar show_front: Boolean property which defaults to True. When True,
    the `source` property will be used by the child Image, when False the
    `back_source` property will be used by the child Image.

    :ivar name: Delegate (read-only) to `card.name` (or None) in order to
    fulfill IFilterable contract. Not used by CarFan.

    :ivar flags: Delegate (read-only) to `card.flags` (or None) in order to
    fulfill IFilterable contract. Not used by CarFan.
    """
    card = Factory.ObjectProperty(allownone=True)
    id = Factory.AliasProperty(ci_getter('id'), ci_setter('id'), bind=['card', 'revision'])
    source = Factory.AliasProperty(ci_getter('source'), ci_setter('source'), bind=['card', 'revision'])
    back_source = Factory.AliasProperty(ci_getter('back_source'), ci_setter('back_source'), bind=['card', 'revision'])
    name = Factory.AliasProperty(ci_getter('name'), ci_setter('name'), bind=['card', 'revision'])
    flags = Factory.AliasProperty(ci_getter('flags'), ci_setter('flags'), bind=['card', 'revision'])

    angle = Factory.NumericProperty(0)

    show_front = Factory.BooleanProperty(True)

    def clear(self):
        """
        Reset attributes to original values. Potentially free-ing the card
        object and ensuring that the id, source, and back_source properties
        will not override a potential future card.

        Used by CardFan when recycling the widget.
        """
        self.card = None
        self._id = self._source = self._back_source = NOVALUE


    def copy_from(self, src):
        for attr in ("size_hint", "pos_hint", "size", "pos"):
            setattr(self, attr, getattr(src, attr, None))
        for attr in ("do_rotation", "do_scale", "scale_min", "scale_max", "do_translation_x", "do_translation_y"):
            setattr(self, attr, getattr(src, attr, None))
        self.transform.set(flat=src.transform.get())
        for attr in ("card", "show_front"):
            setattr(self, attr, getattr(src, attr, None))
        for attr in ("_id", "_source", "_back_source", "_name", "_flags"):
            setattr(self, attr, getattr(src, attr, NOVALUE))
        return self

    def copy(self):
        return self.__class__().copy_from(self)

class CardFanState(Object):
    anim = Attr()
    data = Attr()
    status = Attr() # new, mv, ok, rm, recycle
    widget = Attr()

class CardFan(Factory.FloatLayout):
    """
    Widget for a Fan of cards. Includes various functions for adding cards
    to the fan with animations.

    Fan "shape" is determined by the spacing, min_radius, max_angle
    properties. Additionally, the actual spacing will be adjusted so that
    the fan never exceeds the widget width.
    """
    cards = Factory.ListProperty()
    card_widget = Factory.ObjectProperty('CardImage')
    card_width = Factory.NumericProperty(120)
    card_height = Factory.NumericProperty(180)
    card_size = Factory.ReferenceListProperty(card_width, card_height)

    min_radius = Factory.NumericProperty(-1)
    max_angle = Factory.BoundedNumericProperty(60, min=1, max=360)
    spacing = Factory.NumericProperty(48)
    lift = Factory.NumericProperty(48)

    linear_speed = Factory.NumericProperty(inch(15))
    angular_speed = Factory.NumericProperty(60)
    fade_time = Factory.NumericProperty(0.250)
    max_animation_time = Factory.NumericProperty(2)

    # Informational (read-ony)
    actual_radius = Factory.NumericProperty()
    actual_spacing = Factory.NumericProperty()

    def __init__(self, **kwargs):
        self._widget_cache = []
        self._by_data = {}
        self._by_widget = {}
        self.register_event_type('on_removed')
        self.register_event_type('on_added')
        super().__init__(**kwargs)
        self.redraw = Clock.create_trigger(self._redraw)

    def __len__(self):
        return len(self.cards)

    def insert(self, index, data, *, widget=None):
        state = CardFanState(data=data, widget=widget, status=('mv' if widget else 'new'))
        # TODO: CHECK data
        self._by_data[id(data)] = state
        if widget is not None:
            # TODO: CHECK widget
            self._by_widget[id(widget)] = state
        self.cards.insert(index, data)

    def pop(self, index, recycle=True):
        data = self.cards.pop(index)
        if recycle:
            state = self._by_data.get(id(data), None)
            state.status = 'recycle'
            return data
        else:
            state = self._forget(data, None)
            return state.data, state.widget

    def on_cards(self, obj, val):
        self.redraw()

    def on_removed(self, data, widget):
        pass

    def on_added(self, data, widget):
        pass

    def _animation_complete(self, anim, widget):
        state = self._by_widget.get(id(widget), None)
        if state is None:
            return
        state.anim = None
        if state.status == 'rm':
            self._forget(state.data, widget)
            self.dispatch('on_removed', state.data, state.widget)
        elif state.status == 'recycle':
            self.recycle(state.widget)
            self.dispatch('on_removed', state.data, None)
        elif state.status in ('new', 'mv'):
            state.status = 'ok'
            self.dispatch('on_added', state.data, state.widget)

    def _forget(self, data, widget, remove=True):
        # TODO: Option to ensure not still in cards or children?
        state = self._by_widget.pop(id(widget), None)
        state2 = self._by_data.pop(id(data), None)
        if state is None:
            state = state2
        elif state2 is not None and state is not state2:
            # If this happens we were sloppy somewhere
            raise Exception("Expected consistent state")
        if widget is not None:
            self.remove_widget(widget)
        elif state is not None and state.widget is not None:
            self.remove_widget(state.widget)
        return state

    def on_pos(self, obj, val):
        pass

    def _redraw(self, dt=None):
        self.targets = self.calculate()
        widgets = self.children[:]
        self.clear_widgets()

        keep = set()
        for i, data in enumerate(self.cards):
            state = self._by_data.get(id(data), None)
            if state is None: # data added to cards directly
                state = CardFanState(data=data, widget=self.get_card_widget(), status='new')
            elif state.widget is None:
                state.widget = self.get_card_widget()
                state.status = 'new'

            if state.status is not 'ok':
                self._update_widget(state.widget, data)

            # Update cache for new creations:
            self._by_data[id(data)] = state
            self._by_widget[id(state.widget)] = state
            self.add_widget(state.widget)
            keep.add(id(data))
            keep.add(id(state.widget))

            self._animate_to_target(state, self.targets[i])

        # Any thing to recycle?
        for widget in widgets:
            if id(widget) not in keep:
                state = self._by_widget.get(id(widget), None)
                if state is not None:
                    if state.status == 'rm':
                        # No need to remove widget, already gone from above
                        self._forget(state.data, widget, remove=False)
                        self.dispatch('on_removed', state.data, state.widget)
                    else:
                        # status might be new or ok if data was removed directly from self.cards
                        state.status == 'recycle'
                        if state.anim:
                            state.anim.cancel(widget)  # Kill without triggering complete
                        if widget.opacity > 0:
                            dt = widget.opacity * self.fade_time
                            state.anim = Animation(opacity=0, duration=dt)
                            state.anim.bind(on_complete=self._animation_complete)
                            state.anim.start(widget)
                        else:
                            self.recycle(widget)
                            self.dispatch('on_removed', state.data, None)

    def recycle(self, widget):
        self._forget(None, widget)
        if widget.parent:
            widget.parent.remove_widget(widget)
        if isinstance(widget, ICardFanReset):
            widget.clear()
        # Don't allow the cache to grow forever.
        n = len(self._widget_cache)
        if n < 10 or n < 0.5 * len(self.cards):
            self._widget_cache.append(widget)

    def on_card_widget(self, obj, val):
        # TODO: invalidate all existing widgets
        self._widget_cache = []

    def get_card_widget(self):
        if self._widget_cache:
            return self._widget_cache.pop()
        else:
            return getattr(Factory, self.card_widget)() if isinstance(self.card_widget, str) else self.card_widget()

    def _update_widget(self, widget, data):
        for k, v in data.items():
            setattr(widget, k, v)

    def calculate(self):
        """
        Produce a list of card positions (x and y are the card CENTERS,
        relative to the widget):

            [ (Cx0, Cy0, rot0), (Cx1, Cy1, rot1), ... ]
        """
        if not self.cards:
            return None
        n = len(self.cards)
        # Note the lies: We use a linear length here, but arc length later.
        # Should be close enough and we can fix it later if necessary.
        length_needed = self.card_width + self.spacing * (n - 1)
        spacing = self.spacing

        if self.min_radius > 0 and n > 1:
            radius = max(self.min_radius, length_needed / radians(self.max_angle))
            half_angle = length_needed / radius / 2

            x_width = 2 * radius * math.sin(half_angle)
            if x_width > self.width:
                # Shrink spacing until we fit
                pass

            # "theta": follows the center of the cards, so operates at r_center.
            # "angle": follows the card rotation which follows the card edge which is our "angle" from before.
            r_center = radius - self.card_height / 2

            half_theta = half_angle - self.card_width / radius / 2
            theta_0 = pi_2 + half_theta
            d_theta = -(2 * half_theta) / (n - 1)

            angle_0 = degrees(half_angle)
            d_angle = -(2 * angle_0) / (n - 1)

            x_0 = self.width / 2
            y_0 = self.height / 2 - r_center

            self.actual_radius = radius
            self.actual_spacing = spacing
            return [ (x_0 + r_center * math.cos(theta_0 + i*d_theta), y_0 + r_center * math.sin(theta_0 + i*d_theta), angle_0 + i * d_angle) for i in range(n) ]

        else:
            # x, y are the center of the first card
            x = (self.width - length_needed + self.card_width) / 2
            y = self.height / 2
            # If container is too small, shrink the spacing and rely on lifting to see the cards
            if x < 0 and n >= 2:
                x, spacing = (0, (self.width - self.card_width) / (n - 1))

            self.actual_radius = -1
            self.actual_spacing = spacing
            return [ (x + spacing*i, y, 0) for i in range(n) ]


    def _animate_to_target(self, state, target):
        widget = state.widget
        widget.size_hint = (None, None)
        widget.pos_hint = {}
        anims = []
        if state.status == 'new':
            widget.opacity = 0
            widget.size = self.card_size
            widget.center_x = target[0]
            widget.center_y = target[1]
            widget.rotation = target[2]
            anims.append(Animation(opacity = 1, duration = self.fade_time))

        elif state.status in ('mv', 'ok'):
            times = [ 0.050, self.fade_time ]
            rot = rotation_for_animation(widget.rotation, target[2])
            if not math.isclose(0, abs(widget.rotation - rot)):
                dt = min(self.max_animation_time, abs(widget.rotation - rot) / self.angular_speed)
                times.append(dt)
                anims.append(Animation(rotation = rot, duration = dt))

            dx = abs(widget.center_x - target[0])
            dy = abs(widget.center_y - target[1])
            if dx > 1 or dy > 1:
                dt = min(self.max_animation_time, hypot(dx, dy) / self.linear_speed)
                times.append(dt)
                anims.append(Animation(center_x = target[0], center_y = target[1], duration = dt))

            if widget.opacity != 1:
                dt = self.fade_time * (1-widget.opacity)
                anims.append(Animation(opacity = 1, duration = dt))

            if widget.size != self.card_size:
                anims.append(Animation(width=self.card_width, height=self.card_height, duration = max(times)))

        else:
            raise Exception("Didn't expect status '{}'".format(state.status))

        if anims:
            if state.anim:
                state.anim.cancel(state.widget)  # Kill without triggering complete
            anim = anims.pop()
            for a in anims:
                anim &= a
            anim.bind(on_complete=self._animation_complete)
            state.anim = anim
            anim.start(state.widget)
