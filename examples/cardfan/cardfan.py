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
import kivy.resources
kivy.resources.resource_add_path(os.path.dirname(__file__))
##
import amethyst.ttkvlib.widgets
from amethyst.games.util import random, nonce
from amethyst.ttkvlib.util import rotation_for_animation
from amethyst.core import Object, Attr

Builder.load_string("""
<VLabel@Label>:
    size_hint_y: None
    height: self.texture_size[1]
<VTextInput@TextInput>:
    size_hint_y: None
    height: self.minimum_height

<MainScreen@FloatLayout>:
    BoxLayout:
        orientation: "vertical"

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

            BoxLayout:
                orientation: "vertical"
                size_hint_x: 0.3
                spacing: 32
                BoxLayout:
                    orientation: "horizontal"
                    height: self.minimum_height
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
                BoxLayout:
                    orientation: "vertical"
                    pos_hint: {'x': 0.2, 'top': 1}
                    size_hint: (0.2, 0.4)
                    VLabel:
                        text: "Draw"
                    CardImage:
                        id: draw_pile
                        back_source: 'card-back.png'
                        show_front: False
                BoxLayout:
                    orientation: "vertical"
                    pos_hint: {'x': 0.6, 'top': 1}
                    size_hint: (0.2, 0.4)
                    VLabel:
                        text: "Discard"
                    CardImage:
                        id: discard_pile
                        back_source: 'card-back.png'
                        show_front: False
                CardFan:
                    id: fan
                    size_hint: (1, 0.6)
                    card_widget: 'CardImage'
                    card_size: (draw_pile.width + 75, draw_pile.height + 75)
                    on_added: args[2].show_front = True
                    min_radius: int(min_radius.text or -1)
                    max_angle: int(max_angle.text or 60)
                    spacing: int(spacing.text or 48)
                    lift: int(lift.text or 48)

"""
)

class Card(Object):
    id = Attr(default=nonce)
    name = Attr()
    back_source = Attr(default='card-back.png')

    @property
    def source(self):
        return f"card-{self.name}.png"

class CardFanApp(App):
    def build(self):
        self.main = Factory.MainScreen()
        self.fan = self.main.ids['fan']
        self.draw_pile = self.main.ids['draw_pile']
        self.discard_pile = self.main.ids['discard_pile']
        return self.main

    def add(self, num, widget=None):
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
        # Drawing: copy a card from the draw pile, then move it to the fan
        img = self.fan.get_card_widget()
        img.copy_from(self.draw_pile)
        self.add(random.randrange(1, 6), widget=img)

    def discard(self):
        # Send a card to the discard pile
        if 0 == len(self.fan):
            return
        data, widget = self.fan.pop(random.randrange(0, len(self.fan)), recycle=False)
        widget.opacity = 1
        self.fan.parent.add_widget(widget)
        dt = math.hypot(widget.x-self.discard_pile.x, widget.y-self.discard_pile.y) / self.fan.linear_speed
        anim = Factory.Animation(
            x=self.discard_pile.x,
            y=self.discard_pile.y,
            width=self.discard_pile.width,
            height=self.discard_pile.height,
            rotation=rotation_for_animation(widget.rotation, 0),
            duration=min(2,dt),
        )
        anim.bind(on_complete=lambda *args: self.fan.recycle(widget))
        anim.start(widget)

    def trash(self, which):
        # Poof, into a puff of smoke
        for n, c in enumerate(self.fan.cards):
            if c['card'].name == which:
                self.fan.pop(n)
                return

    def shuffle(self):
        random.shuffle(self.fan.cards)

    def sort(self):
        self.fan.cards = sorted(self.fan.cards, key=lambda data: data['card'].name)


CardFanApp().run()
