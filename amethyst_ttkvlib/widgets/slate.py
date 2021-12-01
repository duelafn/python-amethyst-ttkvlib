# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: GPL-3.0
__all__ = '''
Slate
'''.split()

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
import kivy.app

from amethyst.core.util import get_class

import amethyst_ttkvlib.behaviors.slate

# slate.pos: is position in its container

Builder.load_string('''
<Slate>:
    do_scale: False
    do_collide_after_children: True
    size_hint: None, None

    width: root.content_width
    height: root.content_height + root.header_height

    RelativeLayout:
        id: head_container
        width: root.content_width
        height: root.header_height
        pos: (0, root.content_height)

    RelativeLayout:
        id: content_container
        width: root.content_width
        height: root.content_height
        pos: (0, 0)
''')


class Slate(Factory.PlayerSlateBehavior, Factory.SlateSubwidgetBehavior, Factory.Scatter):
    header = Factory.ObjectProperty()
    content = Factory.ObjectProperty()

    content_class = Factory.ObjectProperty()
    content_width = Factory.NumericProperty(533)
    content_height = Factory.NumericProperty(300)
    content_size = Factory.ReferenceListProperty(content_width, content_height)

    header_class = Factory.ObjectProperty()
    header_height = Factory.NumericProperty(32)

    @property
    def app(self):
        return kivy.app.App.get_running_app()

    def on_content_class(self, obj, cls):
        if isinstance(cls, str):
            cls = getattr(Factory, cls)
        if cls is not None:
            self.content = cls()

    def on_content(self, obj, content):
        container = self.ids['content_container']
        container.clear_widgets()
        container.add_widget(content)

    def on_header_class(self, obj, cls):
        if isinstance(cls, str):
            cls = getattr(Factory, cls)
        if cls is not None:
            self.header = cls()

    def on_header(self, obj, header):
        container = self.ids['head_container']
        container.clear_widgets()
        container.add_widget(header)

    @property
    def slate(self):
        return self
