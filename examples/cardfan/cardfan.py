#!/usr/bin/python3
# -*- coding: utf-8 -*-
import math
import os.path
import warnings
##
warnings.simplefilter('default')
warnings.filterwarnings('ignore', module=r'.*/(?:pint|kivy)/.*')
warnings.filterwarnings('ignore', module=r'(?:babel|pandas|_pytest)\..*')
##
from kivy.config import Config
# Config.set('graphics', 'fullscreen', 'auto')
Config.set('kivy', 'exit_on_escape', 1)
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
import kivy.core.window
import kivy.resources
kivy.resources.resource_add_path(os.path.dirname(__file__))
##
import amethyst.ttkvlib.widgets
from amethyst.games.util import random, nonce
from amethyst.ttkvlib.util import rotation_for_animation
from amethyst.core import Object, Attr

# A kv specification of the layout of our app. Some comments in there for
# those less familiar with kivy
Builder.load_string("""
# Define custom widgets from base widgets with some default parameter values.
<VLabel@Label>:
    size_hint_y: None
    height: self.texture_size[1]
<VTextInput@TextInput>:
    size_hint_y: None
    height: self.minimum_height

# Make a clickable version of our CardImage for the draw and discard piles.
<ClickCardImage@ButtonBehavior+CardImage>:

<MainScreen@FloatLayout>:
    BoxLayout:
        orientation: "vertical"

        # We start with a row of buttons across the top which, on press,
        # each call a method of our app. "app", "self", and "root" are
        # special variables
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: 100
            Button:
                text: "Add a '1'"
                on_press: app.add(1)
            Button:
                text: "Add a '2'"
                on_press: app.add(2)
            Button:
                text: "Remove a '2'"
                on_press: app.trash(2)

            Button:
                text: "Draw"
                on_press: app.draw()
            Button:
                text: "Discard Random"
                on_press: app.discard()

            Button:
                text: "Shuffle Hand"
                on_press: app.shuffle()
            Button:
                text: "Sort Hand"
                on_press: app.sort()

        BoxLayout:
            orientation: "horizontal"
            padding: (0, 32, 0, 16)

            # Vertically, we have a set of text inputs which (later) we
            # will feed directly (without validation) into the fan parameters.
            BoxLayout:
                orientation: "vertical"
                size_hint_x: 0.3
                spacing: 32
                BoxLayout:
                    orientation: "horizontal"
                    VLabel:
                        text: "Min radius"
                    VTextInput:
                        id: min_radius
                        text: "2000"
                    VLabel:
                        text: "Actual: {:.2f}".format(fan.actual_radius)
                BoxLayout:
                    orientation: "horizontal"
                    VLabel:
                        text: "Max angle"
                    VTextInput:
                        id: max_angle
                        text: "60"
                    Label:
                BoxLayout:
                    orientation: "horizontal"
                    VLabel:
                        text: "Spacing"
                    VTextInput:
                        id: spacing
                        text: "48"
                    VLabel:
                        text: "Actual: {:.2f}".format(fan.actual_spacing)
                BoxLayout:
                    orientation: "horizontal"
                    VLabel:
                        text: "Lift"
                    VTextInput:
                        id: lift
                        text: "48"
                    Label:
                Label:

            RelativeLayout:
                size_hint_x: 0.7
                # Simple draw and discard piles. In addition to creating
                # visible on-screen targets. They also give us location
                # information for when we draw and discard in the app.
                BoxLayout:
                    orientation: "vertical"
                    pos_hint: {'x': 0.2, 'top': 1}
                    size_hint: (0.2, 0.4)
                    VLabel:
                        text: "Draw"
                    ClickCardImage:
                        id: draw_pile
                        back_source: 'card-back.png'
                        show_front: False
                        on_press: app.draw()

                BoxLayout:
                    orientation: "vertical"
                    pos_hint: {'x': 0.6, 'top': 1}
                    size_hint: (0.2, 0.4)
                    VLabel:
                        text: "Discard"
                    ClickCardImage:
                        id: discard_pile
                        back_source: 'card-back.png'
                        show_front: False
                        on_press: app.discard()

                # Finally the CardFan itself. We set some desired
                # properties, make sure the card is face-up when it gets
                # moved into the fan, and set some parameters from the text
                # input boxes above.
                CardFan:
                    id: fan
                    size_hint: (1, 0.6)
                    card_widget: 'CardImage'
                    card_width:  draw_pile.width + 75
                    card_height: draw_pile.height + 75
                    lifted_cards: app.selected + [app.hovered]

                    on_card_add: args[3].show_front = True

                    min_radius: int(min_radius.text or -1)
                    max_angle: int(max_angle.text or 60)
                    spacing: int(spacing.text or 48)
                    lift: int(lift.text or 48)

"""
)

# Card is an immutable object for us. If we tried modifying it, the kivy
# widgets would not automatically pick up the changes since we are using
# standard attributes and properties (not kivy `Property()` objects).
class Card(Object):
    id = Attr(default=nonce)
    name = Attr()
    back_source = Attr(default='card-back.png')

    @property
    def source(self):
        return f"card-{self.name}.png"


class CardFanApp(App):
    hovered = Factory.NumericProperty(None, allownone=True)
    selected = Factory.ListProperty()

    def build(self):
        kivy.core.window.Window.bind(on_key_down=self.on_key_down)
        self.main = Factory.MainScreen()
        self.fan = self.main.ids['fan']
        self.fan.bind(on_card_select=self.on_card_select)
        self.fan.bind(on_card_hover=self.on_card_hover)
        self.draw_pile = self.main.ids['draw_pile']
        self.discard_pile = self.main.ids['discard_pile']
        return self.main

    def add(self, num, widget=None):
        # We can just `insert()` dictionaries into the fan. This can be
        # done using insert or directly manipulating fan.cards. These cards
        # will just appear in the fan using a fade-in.
        card = Card(name=num)
        n = 0
        # Keep them sorted when drawing
        for n, c in enumerate(self.fan.cards):
            if c['card'].name > num:
                break
        else:
            n = len(self.fan)
        self.fan.insert(n, dict(card=card), widget=widget)

    def draw(self):
        # If we instead want an animated draw or deal of a card, we have to
        # get ahold of a valid widget, configure it with its starting
        # position, then insert it into the fan. A `copy_from()` method on
        # the draw pile which just clones all interesting attributes makes
        # this straight forward since the fan will handle animation for us.
        img = self.fan.get_card_widget()
        img.copy_from(self.draw_pile)
        self.add(random.randrange(1, 6), widget=img)

    def trash(self, which):
        # Poof, into a puff of smoke. Popping a card from the fan will
        # remove the data from `cards` and, after a fade-out animation,
        # recycle the widget for later use.
        for n, c in enumerate(self.fan.cards):
            if c['card'].name == which:
                self.fan.pop(n) # returns the dict() we inserted above, but we don't need it
                return

    def discard(self, index=None):
        # When discarding we have more work to do ourselves. If we pop with
        # `recycle=False`, the fan will return our original data dictionary
        # and also the widget for the card.
        if 0 == len(self.fan):
            return
        if index is None:
            index = random.randrange(0, len(self.fan))
        data, widget = self.fan.pop(index, recycle=False)
        widget.opacity = 1
        # The widget has already been removed from the fan, so we have to
        # reparent it into some suitable location. The fan's parent will
        # usually be a good call.
        self.fan.parent.add_widget(widget)
        # Finally, we want an animation sending the card into the discard pile.
        dt = math.hypot(widget.x-self.discard_pile.x, widget.y-self.discard_pile.y) / self.fan.linear_speed
        anim = Factory.Animation(
            x=self.discard_pile.x,
            y=self.discard_pile.y,
            width=self.discard_pile.width,
            height=self.discard_pile.height,
            rotation=rotation_for_animation(widget.rotation, 0),
            duration=min(2,dt),
        )
        anim.bind(on_complete=lambda *args: self.discard_complete(data['card'], widget))
        anim.start(widget)

    def discard_complete(self, card, widget):
        # When the discard animation completes, we can recycle the card
        # widget to the fan and then add the card data to the discard pile.
        # Here we don't bother remembering what is in the discard, we just
        # show the most recent discard.
        self.fan.recycle(widget)
        self.discard_pile.card = card
        self.discard_pile.show_front = True

    def shuffle(self):
        # The fan will automatically handle any changes to its `cards`
        # property, so reordering the list will reoder the cards (with
        # animation)
        random.shuffle(self.fan.cards)

    def sort(self):
        # Just more reordering
        self.fan.cards = sorted(self.fan.cards, key=lambda data: data['card'].name)

    def on_card_select(self, obj, how, index):
        if how == 'tap':
            if index in self.selected:
                self.selected.remove(index)
            else:
                self.selected.append(index)
        else:
            self.discard(index)

    def on_card_hover(self, obj, hover, index):
        if hover:
            self.hovered = index
        else:
            self.hovered = None

    def on_key_down(self, win, key, scancode, string, modifiers):
        if key == 292: # F11
            win.fullscreen = 'auto' if win.fullscreen is False else False
            win.update_viewport()
            return True

CardFanApp().run()
