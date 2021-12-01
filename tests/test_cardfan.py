#!/usr/bin/python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0

import sys
from os.path import dirname, abspath, join
sys.path.insert(1, dirname(dirname(abspath(__file__))))
sys.argv = [ sys.argv[0] ]  # clear argv else kivy gets confused

import unittest
from kivy.factory import Factory
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.base import EventLoop

from amethyst_ttkvlib.widgets.cardfan import CardFan, CardImage, ICardFanReset

class Card(object):
    def __init__(self, id, source):
        self.id = id
        self.source = source


class MyTest(GraphicUnitTest):

    def test_CardImage(self):
        img = CardImage()
        img.card = Card('12345', 'foo.png')

        self.assertEqual(img.id, '12345')
        self.assertEqual(img.source, 'foo.png')
        self.assertIsNone(img.back_source)

        img.id = '123456'
        self.assertEqual(img.id, '123456')
        self.assertEqual(img.card.id, '12345')

        img.clear()
        self.assertIsNone(img.id)
        self.assertIsNone(img.card)
        self.assertIsNone(img.source)
        self.assertIsNone(img.back_source)


if __name__ == '__main__':
    unittest.main()
