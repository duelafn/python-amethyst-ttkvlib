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
import time
import warnings
from math import pi, radians, degrees, hypot, sin, cos
pi_2 = pi/2

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import inch
from kivy.clock import Clock
import kivy.graphics

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
    default_drag_distance: min(inch(.125), self.card_width/10, self.card_height/10)
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

class CardTarget(object):
    __slots__ = ('x', 'y', 'angle', 'rotation', 'sin', 'cos')
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        if abs(angle) < 0.001:  # Snap to zero
            self.angle = 0
            self.rotation = 0
            self.sin = 0
            self.cos = 1
        else:
            self.angle = angle
            self.rotation = degrees(angle)
            self.sin = sin(angle)
            self.cos = cos(angle)
    def __str__(self):
        return "({}, {}) radian={:.3f} degree={:.17f}".format(self.x, self.y, self.angle, self.rotation)

    def rotated_vector(self, x, y):
        return (self.cos * x - self.sin * y, self.sin * x + self.cos * y)

    def rotated_size(self, w, h):
        return (abs(self.cos) * w + abs(self.sin) * h, abs(self.sin) * w + abs(self.cos) * h)


class CardFanState(object):
    __slots__ = ('anim', 'data', 'status', 'widget', 'target', 'index')
    def __init__(self, anim=None, data=None, status=None, widget=None, target=None, index=None):
        self.anim = anim
        self.data = data
        self.status = status # new, mv, ok, rm, recycle
        self.widget = widget
        self.target = target
        self.index = index

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

    true_center = Factory.BooleanProperty(False)  # When false, rotated cards dip below baseline
    min_radius = Factory.NumericProperty(-1)
    max_angle = Factory.BoundedNumericProperty(60, min=1, max=360)
    spacing = Factory.NumericProperty(48)
    lift = Factory.NumericProperty(48)

    linear_speed = Factory.NumericProperty(inch(15))
    fade_time = Factory.NumericProperty(0.250)
    max_animation_time = Factory.NumericProperty(2)
    long_press_time = Factory.NumericProperty(0.75)
    drag_distance = Factory.NumericProperty(None, allownone=True)
    default_drag_distance = Factory.NumericProperty(inch(.125))

    lifted_cards = Factory.ListProperty()

    # Informational (read-ony)
    actual_radius = Factory.NumericProperty()
    actual_spacing = Factory.NumericProperty()

    circle_origin_x = Factory.NumericProperty(0)
    circle_origin_y = Factory.NumericProperty(0)
    circle_origin = Factory.ReferenceListProperty(circle_origin_x, circle_origin_y)

    def __init__(self, **kwargs):
        self._widget_cache = []
        self._by_data = {}
        self._by_widget = {}
        self._redraw_instant = False
        self.register_event_type('on_card_add')
        self.register_event_type('on_card_remove')
        self.register_event_type('on_card_press')
        self.register_event_type('on_card_long_press')
        self.register_event_type('on_card_drag')
        self.register_event_type('on_card_drop')
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

    def on_lifted_cards(self, obj, val):
        self.redraw()


    def on_card_add(self, index, data, widget):
        """
        Card newly added to the fan. This event is triggered after the card
        animation (fade in or move to position) has completed.

        NOTE: The index passed to this function is the card's index at the
        time that the function is called. That index is may change if cards
        are added or removed from the fan.
        """
        pass

    def on_card_remove(self, data, widget):
        """
        Card removed from the fan. This function is called after the widget
        is removed from the fan's list of children.

        If the card is to be recycled, this function will be called after
        the fade-out animation completes. In this case, the widget
        parameter will be None.

        If the card was removed without recycling (for instance, via
        `.pop(recycle=False)`), then this function will be called while the
        card is still opaque and in position. However, since the widget no
        longer has a parent, it will not be visible in the next render
        frame unless it is added to another suitable parent. At that point,
        it is the responsibility of the caller to manage the widget.

        Note: typically, you will either handle the orphaned widget either
        when you call .pop() or in the .on_card_remove() function but not
        both.
        """
        pass

    def on_card_press(self, index, data, widget, touch):
        """
        Called when the user selects a card by tap or gesture. This widget
        will not automatically add the card to the list of lifted_cards,
        that should be done by this callback if appropriate.

        The `select` parameter is set to True if the card index is
        currently ABSENT from the lifted_cards list (meaning the function
        call is a selection request).

        :param how: Method of selection. Is one of: "tap" or "gesture"
        """
        pass

    def on_card_long_press(self, index, data, widget, touch):
        pass

    def on_card_drag(self, index, data, widget, touch):
        pass

    def on_card_drop(self, index, data, widget, touch):
        pass


    def _animation_complete(self, anim, widget):
        state = self._by_widget.get(id(widget), None)
        if state is None:
            return
        state.anim = None
        if state.status == 'rm':
            self._forget(state.data, widget)
            self.dispatch('on_card_remove', state.data, state.widget)
        elif state.status == 'recycle':
            self.recycle(state.widget)
            self.dispatch('on_card_remove', state.data, None)
        elif state.status in ('new', 'mv'):
            state.status = 'ok'
            self._instant_to_target(state)
            self.dispatch('on_card_add', state.index, state.data, state.widget)

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

    def on_size(self, obj, val):
        # Either we did a full-screen resize in which case a discontinuous
        # jump in positions is OK, or the fan is being resized slowly (a
        # scatter or animation) in which case we don't need to stack animations.
        self._redraw_instant = True
        self.redraw()

    def _redraw(self, dt=None):
        targets = self.calculate()
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
            state.index = i
            state.target = targets[i]

            # Update cache for new creations:
            self._by_data[id(data)] = state
            self._by_widget[id(state.widget)] = state
            self.add_widget(state.widget)
            keep.add(id(data))
            keep.add(id(state.widget))

            self._animate_to_target(state)
        # Done redrawing, clear flag if present
        self._redraw_instant = False

        # Any thing to recycle?
        for widget in widgets:
            if id(widget) not in keep:
                state = self._by_widget.get(id(widget), None)
                if state is not None:
                    if state.status == 'rm':
                        # No need to remove widget, already gone from above
                        self._forget(state.data, widget, remove=False)
                        self.dispatch('on_card_remove', state.data, state.widget)
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
                        else: # Unlikely - only if user triggers a fade before removing
                            self.recycle(widget)
                            self.dispatch('on_card_remove', state.data, None)

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
        self.clear_widgets()
        self._by_data.clear()
        self._by_widget.clear()
        self._widget_cache.clear()
        self.redraw()

    def get_card_widget(self):
        if self._widget_cache:
            return self._widget_cache.pop()
        else:
            return getattr(Factory, self.card_widget)() if isinstance(self.card_widget, str) else self.card_widget()

    def _update_widget(self, widget, data):
        for k, v in data.items():
            setattr(widget, k, v)


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            index = self.card_at_point(*touch.pos)
            state = self._by_data.get(id(self.cards[index])) if index is not None else None
            if index is not None and state is not None:
                touch.grab(self)
                touch.ud['cardfan:state'] = state
                touch.ud['cardfan:type'] = None
                if self.long_press_time:
                    touch.ud['cardfan:lpcb'] = Clock.schedule_once(
                        lambda *args: self._maybe_long_press(touch),
                        self.long_press_time
                    )

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            state = touch.ud['cardfan:state']
            if touch.ud['cardfan:type'] is None:
                # Taxicab metric is fine
                dx, dy = touch.ox - touch.x, touch.oy - touch.y
                dist = abs(dx) + abs(dy)
                if self.drag_distance != 0 and dist > (self.drag_distance or self.default_drag_distance):
                    touch.ud['cardfan:type'] = 'drag'
                    self.dispatch('on_card_drag', state.index, state.data, state.widget, touch)
                    if touch.ud['cardfan:type'] == 'drag':
                        if state.anim:
                            state.anim.cancel(state.widget)  # Kill without triggering complete
                        state.widget.x += dx
                        state.widget.y += dy
            elif touch.ud['cardfan:type'] == 'drag':
                state.widget.x += touch.dx
                state.widget.y += touch.dy

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            state = touch.ud['cardfan:state']
            longpress = touch.ud.pop('cardfan:lpcb', None)
            if longpress:
                longpress.cancel()
            if touch.ud['cardfan:type'] is None:
                self.dispatch('on_card_press', state.index, state.data, state.widget, touch)
            elif touch.ud['cardfan:type'] == 'drag':
                self.dispatch('on_card_drop', state.index, state.data, state.widget, touch)
            elif touch.ud['cardfan:type'] == 'longpress':
                pass
            else:
                warnings.warn("CardFan: Unexpected event type".format(touch.ud['cardfan:type']))
            self.redraw()

    def _maybe_long_press(self, touch):
        if touch and not touch.ud['cardfan:type']:
            touch.ud['cardfan:type'] = 'longpress'
            state = touch.ud['cardfan:state']
            self.dispatch('on_card_long_press', state.index, state.data, state.widget, touch)
            del touch.ud['cardfan:lpcb']

    def card_at_point(self, x, y):
        """
        Returns the card number (index in the cards list) of the card
        visible at the given touch position.
        """
        # Modified from kivy.uix.widget.Widget#export_to_png()
        n = len(self.children)-1
        if not hasattr(self, "_fbo"):
            self._fbo = kivy.graphics.Fbo(size=self.size, with_stencilbuffer=True)
        self._fbo.size = self.size   # Kivy recreates fbo only if size changes - convenient

        for i, chld in enumerate(self.children):
            # First try the cheap rectangular bounding-box test
            if chld.collide_point(x, y):
                canvas_index = self.canvas.indexof(chld.canvas)
                if canvas_index > -1:
                    self.canvas.remove(chld.canvas)

                try:
                    with self._fbo:
                        kivy.graphics.ClearColor(0, 0, 0, 0)
                        kivy.graphics.ClearBuffers()

                    self._fbo.add(chld.canvas)
                    try:
                        self._fbo.draw()
                        if self._fbo.get_pixel_color(x, y)[3] > 50:
                            return n-i
                    finally:
                        self._fbo.remove(chld.canvas)
                finally:
                    if canvas_index > -1:
                        self.canvas.insert(canvas_index, chld.canvas)
        return None


    def calculate(self):
        """
        Produce a list of card positions (x and y are the card LEFT and
        BOTTOM):

            [ (x0, y0, rot0), (x1, y1, rot1), ... ]


        The scatter widget rotates about the center of the card.

                       *\
                     -/  \
                   -/     \
                 -/        \
               -/           \
             -/              \
            @                 \
             \                 \
              \                 \
               \        @        \
                \                 \
                 \                 \
                  \                 \
                   \                 *
                    \              -/
                     \           -/
                      \        -/
                       \     -/
            (x, y)      \  -/
            *            */

        We get trouble if we try animating center position, rotation, and
        scale all at once. It is more stable if we animate position of
        lower-left (x, y).

        0 <= rotation <= 90: x from top-left, y from bottom-left

           x = center - cos(θ) card_width / 2 - sin(θ) card_height / 2
           y = center - sin(θ) card_width / 2 - cos(θ) card_height / 2

        All other cases similar, we can simplify to:

           x = center - (abs(cos(θ)) card_width + abs(sin(θ)) card_height) / 2
           y = center - (abs(sin(θ)) card_width + abs(cos(θ)) card_height) / 2

        """
        if not self.cards:
            return ()
        n = len(self.cards)
        # Full card width for the top card plus one spacing for each other card
        length_needed = self.card_width + self.spacing * (n - 1)
        spacing = self.spacing

        if self.min_radius > 0 and n > 1:
            # "angle" is spread of cards passing through the CENTER of the
            # cardes since it is easier to work with. Thus, only the
            # spacing needs covered by the angle.
            o_radius = max(self.min_radius, self.spacing * (n - 1) / radians(self.max_angle))
            half_angle = self.spacing * (n - 1) / o_radius / 2
            # Radius through center
            c_radius = o_radius - self.card_height / 2

            # How wide will we be? We may need to shrink the spacing to
            # fit. If configured for greater than 180° fan, assume game is
            # ready for the size. Otherwise, reducing the spacing can help.
            if half_angle < pi_2:
                # rotation of the card, furthest point on X from center (twice for left and right)
                beyond_center = cos(pi_2 + half_angle) * self.card_width + sin(pi_2 + half_angle) * self.card_height
                available_width = self.width - beyond_center
                # width from left card center to right card center
                width = 2 * c_radius * sin(half_angle)
                if width > available_width:
                    half_angle = math.asin( available_width / 2 / c_radius )
                    spacing = available_width / (n - 1)

            # Position offsets
            x_0 = self.width / 2
            y_0 = self.height / 2 - c_radius

            # Calculate positions
            res = []
            d_theta = -(2 * half_angle) / (n - 1)
            y_min = c_radius - self.card_height/2
            for i in range(n):
                target = CardTarget(x_0, y_0, half_angle + i*d_theta)
                w, h = target.rotated_size(self.card_width, self.card_height)
                target.x += c_radius * cos(pi_2 + target.angle) - w/2
                target.y += c_radius * sin(pi_2 + target.angle) - h/2
                if target.y < y_min:
                    y_min = target.y
                if i in self.lifted_cards:
                    dx, dy = target.rotated_vector(0, self.lift)
                    target.x += dx
                    target.y += dy
                res.append(target)

            # Rotated cards dip below baseline, optionally shift the cards
            # up to true center.
            if self.true_center:
                height = c_radius + self.card_height/2 - y_min
                y_off  = (height - self.card_height)/2
                for t in res:
                    t.y += y_off

            self.actual_radius = o_radius
            self.actual_spacing = spacing
            self.circle_origin_x = x_0
            self.circle_origin_y = y_0
            return res

        else:
            # x, y are the bottom-left of the first card
            x = (self.width - length_needed) / 2
            y = self.height / 2 - self.card_height / 2
            # If container is too small, shrink the spacing and rely on lifting to see the cards
            if x < 0 and n >= 2:
                x, spacing = (0, (self.width - self.card_width) / (n - 1))

            self.actual_radius = -1
            self.actual_spacing = spacing
            self.circle_origin_x = x
            self.circle_origin_y = y
            return [ CardTarget(x + spacing*i, y + self.lift * (i in self.lifted_cards)) for i in range(n) ]


    def _instant_to_target(self, state):
        widget = state.widget
        widget.size_hint = (None, None)
        widget.pos_hint = {}
        widget.opacity = 1
        widget.size = self.card_size
        widget.x = state.target.x
        widget.y = state.target.y
        widget.rotation = state.target.rotation

    def _animate_to_target(self, state):
        if self._redraw_instant and state.status == 'ok':
            self._instant_to_target(state)
            return

        widget = state.widget
        widget.size_hint = (None, None)
        widget.pos_hint = {}
        anims = []

        if state.status == 'new':
            widget.opacity = 0
            widget.size = self.card_size
            widget.x = state.target.x
            widget.y = state.target.y
            widget.rotation = state.target.rotation
            anims.append(Animation(opacity = 1, duration = self.fade_time))

        elif state.status in ('mv', 'ok'):
            times = [ 0.050, self.fade_time ]

            # Rotation "corrects" the x and y position to preserve the
            # center point (or something). In any case, if we finish our
            # translation before finishing our rotation, the cards aren't
            # in the right place. Therefore, make sure the rotation is done
            # before we finish translation. If we won't have a translation,
            # force the rotation then reconsider whether we need a translation.
            dx = abs(widget.x - state.target.x)
            dy = abs(widget.y - state.target.y)
            if dx <= 1 and dy <= 1:
                widget.rotation = state.target.rotation
                dx = abs(widget.x - state.target.x)
                dy = abs(widget.y - state.target.y)
            if dx > 1 or dy > 1:
                dt = min(self.max_animation_time, hypot(dx, dy) / self.linear_speed)
                times.append(dt)
                anims.append(Animation(x = state.target.x, y = state.target.y, duration = dt))

                rot = rotation_for_animation(widget.rotation, state.target.rotation)
                if abs(widget.rotation - rot) > 0.1: # 0.1 degree is sufficient precision
                    anims.append(Animation(rotation = rot, duration = 0.8 * dt))

            if widget.opacity != 1:
                dt = self.fade_time * (1-widget.opacity)
                anims.append(Animation(opacity = 1, duration = dt))

            if widget.size != self.card_size:
                anims.append(Animation(width=self.card_width, height=self.card_height, duration = 0.8 * max(times)))

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
