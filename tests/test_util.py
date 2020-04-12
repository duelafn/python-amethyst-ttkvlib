#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0

import sys
from os.path import dirname, abspath, join
sys.path.insert(1, dirname(dirname(abspath(__file__))))

import unittest

from amethyst.ttkvlib.util import rotation_for_animation


class MyTest(unittest.TestCase):

    def test_rotation_for_animation(self):
        self.assertEqual(rotation_for_animation(350, 10), 370)
        self.assertEqual(rotation_for_animation(350, -10), 350)
        self.assertEqual(rotation_for_animation(350, 0), 360)
        self.assertEqual(rotation_for_animation(360, 0), 0)

        self.assertEqual(rotation_for_animation(10, 10), 10)
        self.assertEqual(rotation_for_animation(10, -10), -10)
        self.assertEqual(rotation_for_animation(10, 0), 0)
        self.assertEqual(rotation_for_animation(0, 360), 0)

        self.assertEqual(rotation_for_animation(10, 350), -10)
        self.assertEqual(rotation_for_animation(10, 350), -10)
        self.assertEqual(rotation_for_animation(10, 350), -10)
        self.assertEqual(rotation_for_animation(0, 350), -10)

        self.assertEqual(rotation_for_animation(10, 100), 100)
        self.assertEqual(rotation_for_animation(10, -100), -100)
        self.assertEqual(rotation_for_animation(10, 100), 100)
        self.assertEqual(rotation_for_animation(0, 100), 100)


if __name__ == '__main__':
    unittest.main()

