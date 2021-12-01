# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: GPL-3.0
__all__ = '''
color
contrast_bw
darken
lighten
mix_colors
rotation_for_animation
'''.split()

from kivy.utils import get_color_from_hex

from amethyst_games import random


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
    a, b = a % 360, b % 360
    if b - a < -180:
        return b + 360
    if b - a > 180:
        return b - 360
    return b





COLOR_LIST = [ get_color_from_hex(x) for x in (
    'e50000',  # red
    '0343df',  # blue
    'ffff14',  # yellow
    '7e1e9c',  # purple
    '15b01a',  # green
    'f97306',  # orange
    '653700',  # brown
    '029386',  # teal
    'ff81c0',  # pink
    '95d0fc',  # light blue
    'bf77f6',  # light purple
    '96f97b',  # light green
    'd1b26f',  # tan
    '929591',  # grey
)]
def color(i=None):
    """Just a color list. If i is None, returns a random color."""
    if i is None:
        return random.choice(COLOR_LIST)
    return COLOR_LIST[i % len(COLOR_LIST)]

# Color functions inspired by the Perl module "Color::Calc"
def contrast_bw(color, cut=0.5):
    """
    Returns black `(0,0,0,color[3])` or white `(1,1,1,color[3])`, whichever
    has the higher contrast to `color`. Alpha value of color is preserved.

    This is done by returning black if the grey value of `color` is above
    `cut` and white otherwise.

    The default for `cut` is .5.
    """
    grey = color[0]*.3 + color[1]*.59 + color[2]*.11
    return (1,1,1,color[3]) if grey < cut else (0,0,0,color[3])

def lighten(color, mix=0.5):
    """
    Returns a lighter version of `color`, i.e. returns
    `mix_colors(color,[1,1,1],mix)`.

    The optional `mix` parameter can be a value between 0.0 (use `color`
    only) and 1.0 (use white only), the default is 0.5.
    """
    return mix_colors(color, (1,1,1, color[3]), mix=0.5)

def darken(color, mix=0.5):
    """
    Returns a darker version of `color`, i.e. returns
    `mix_colors(color,[0,0,0],mix)`.

    The optional `mix` parameter can be a value between 0.0 (use `color`
    only) and 1.0 (use black only), the default is 0.5.
    """
    return mix_colors(color, (0,0,0, color[3]), mix=0.5)

def mix_colors(color1, color2, mix=0.5):
    """
    Returns a color that is the mixture of `color1` and `color2`.

    The optional `mix` parameter can be a value between 0.0 (use `color1`
    only) and 1.0 (use `color2` only), the default is 0.5.
    """
    return (
        (color1[0] + (color2[0]-color1[0])*mix),
        (color1[1] + (color2[1]-color1[1])*mix),
        (color1[2] + (color2[2]-color1[2])*mix),
        (color1[3] + (color2[3]-color1[3])*mix),
    )
