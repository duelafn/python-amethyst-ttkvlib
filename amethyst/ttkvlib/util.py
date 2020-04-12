# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: GPL-3.0
__all__ = '''
rotation_for_animation
'''.split()


def rotation_for_animation(a, b):
    """
    Choose a rotational branch angle equivalent to `b` but is closest to
    `a`. Useful for animating rotations cleanly.

       target = rotation_for_animation(widget.rotation, target_rotation)
       anim = Animation(rotation=target)
       anim.start(widget)

    Without this function, an Animation of a rotation may not always do
    what you want if. For example, if `widget.rotation = 330`, then

       Animation(rotation=0).start(widget)

    Will rotate the object all the way through 330 degrees to get to 0
    instead of taking the short 30 degree path to 360.
    """
    # Note: 0..360 even if a,b negative
    # Ensure 0 <= a < 360 - we might want to lift this restriction some day
    a, b = a%360, b%360
    if b - a < -180:
        return b + 360
    if b - a > 180:
        return b - 360
    return b
