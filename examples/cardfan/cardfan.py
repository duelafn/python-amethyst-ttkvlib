#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os.path
import warnings
##
warnings.simplefilter('default')
warnings.filterwarnings('ignore', module=r'.*/(?:pint|kivy)/.*')
warnings.filterwarnings('ignore', module=r'(?:babel|pandas|_pytest)\..*')
##
from kivy.config import Config
Config.set('kivy', 'exit_on_escape', 1)
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder
import kivy.resources
kivy.resources.resource_add_path(os.path.dirname(__file__))
##
import amethyst.ttkvlib.widgets
from amethyst.games.util import random, nonce
from amethyst.core import Object, Attr

Builder.load_string("""
<VLabel@Label>:
    size_hint_y: None
    height: self.texture_size[1]
<VTextInput@TextInput>:
    size_hint_y: None
    height: self.minimum_height

<MainScreen@BoxLayout>:
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

        FloatLayout:
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
                pos: self.parent.pos
                size_hint: (1, 0.6)
                card_widget: 'CardImage'
                card_size: draw_pile.size
                on_ready: args[2].show_front = True
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
        print(self.draw_pile.size)

        card = Card(name=num)
        n = 0
        # Keep them sorted when drawing
        for n, c in enumerate(self.fan.cards):
            if c['card'].name > num: break
        self.fan.insert(n, dict(card=card), widget=widget)

    def draw(self):
        # Drawing: copy a card from the draw pile, then move it to the fan
        img = self.fan.get_card_widget()
        img.copy_from(self.draw_pile)
        self.add(random.randrange(1, 6), widget=img)

    def discard(self):
        pass
    def shuffle(self):
        pass
    def sort(self):
        pass


CardFanApp().run()
