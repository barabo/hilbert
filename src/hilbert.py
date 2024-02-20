#!/usr/bin/env python

"""
This code produces a Hilbert curve tile pattern image.
"""

from PIL import Image, ImageDraw
from PIL.ImageColor import getrgb as rgb
import random
import sys


""" A mapping of shapes to sub-shapes and order of visitation.

For example, a 'u' shape is composed of 4 sub-shapes which look like:
  +---+---+
  | > | < |
  +---+---+
  | u | u |
  +---+---+

The order in which they are 'visited' or 'drawn' is counterclockwise here, but
is different for each different configuration.

This structure maps the outermost shape to the inner sub-shapes and ordinality.

HILBERT: dict: (x, y): (i, sub-shape)
  x - int, the x coordinate within the 4x4 grid
  y - int, the y coordinate within the 4x4 grid
  i - int, the order in which the sub-shape is visited when drawing the curve
  sub-shape - str, the shape of the pattern within the quadrant (x, y).
"""
HILBERT = {
    "u": {(0, 0): (0, ">"), (0, 1): (1, "u"), (1, 0): (3, "<"), (1, 1): (2, "u")},
    "<": {(0, 0): (2, "<"), (0, 1): (1, "<"), (1, 0): (3, "u"), (1, 1): (0, "n")},
    "n": {(0, 0): (2, "n"), (0, 1): (3, ">"), (1, 0): (1, "n"), (1, 1): (0, "<")},
    ">": {(0, 0): (0, "u"), (0, 1): (3, "n"), (1, 0): (1, ">"), (1, 1): (2, ">")},
}


def Hilbert(x, y, shape, order):
    """Returns the hilbert number of a point in an image.

    The Hilbert number is the order in which a point is visited when following the
    curve.

    Args:
      x: int, the x coordinate
      y: int, the y coordinate
      shape: str, the 'shape' of the curve (one of '><un')
      order: int, the power of 2 order of the size of the square curve.

    Returns:
      int, the order in which the point was visited when drawing the curve.
    """
    position = 0
    for i in range(order - 1, -1, -1):
        position <<= 2
        _x = 1 if x & (1 << i) else 0
        _y = 1 if y & (1 << i) else 0
        _position, shape = HILBERT[shape][(_x, _y)]
        position |= _position
    return position


class Pattern(object):
    """A Hilbert curve pattern for use rendering images."""

    # The ratio of grout width / tile width is equal to: 1 / (scale - 1)
    scale = 9

    def __init__(self, order):
        left = self.GetPath(order, "<", 0)
        right = self.GetPath(order, ">", 2**order)
        self.path = left + right
        z = self.scale
        self.points = [(z * (x + 1), z * (y + 1)) for (x, y) in self.path]

    def GetPath(self, order, shape, _x):
        """Returns the coordinates of the points in order of visitation.

        This allows the points to be used to define a polygon in the ImageDraw
        module.

        Args:
          order: int, the power of 2 order of the pattern.
          shape: str, one of '><nu' - the 'shape' of the pattern.
          _x: int, an offset to apply to the x of each point.
        """
        width = 2**order
        points = [(x, y) for x in range(0, width) for y in range(0, width)]
        path = [(Hilbert(x, y, shape, order), (x + _x, y)) for (x, y) in points]
        return [x for (_, x) in sorted(path)]


# Colors for the tiles and grout lines.
GROUT = rgb("#232023")
INSIDE = [rgb(x) for x in ["black"]]
OUTSIDE = [rgb(x) for x in ["grey", "darkgrey"]]
OUTSIDE = [
    (161, 139, 232),  # purple
    (172, 219, 110),  # light green
    (189, 189, 189),  # light grey
    (247, 205,  85),  # golden
    (213, 130, 194),  # pink
    (127, 198, 174),  # cyan
    ( 26,  69, 167),  # blue
    (177, 221, 242),  # light blue
    (127, 162, 186),  # gunmetal
]


def main():
    order = int(sys.argv[1])  # should be a small number between 2 and 7
    pattern = Pattern(order)

    # Create an empty image of the correct size and background color.
    image_type = "PNG"
    filename = f"hilbert-{order}.{image_type.lower()}"
    x = max([x for (x, _) in pattern.points]) + pattern.scale
    y = max([y for (_, y) in pattern.points]) + pattern.scale
    image = Image.new("RGB", (x + 1, y + 1), OUTSIDE[0])
    image.save(filename, image_type)

    # Draw the hilbert curve as a polygon.
    image = Image.open(filename)
    draw = ImageDraw.Draw(image)
    draw.polygon(pattern.points, outline=GROUT, fill=INSIDE[0])

    # Draw the grout lines.
    width = x
    height = y
    for x in set([0, x] + [x for (x, _) in pattern.points]):
        draw.line([(x, 0), (x, height)], width=1, fill=GROUT)
    for y in set([0, y] + [y for (_, y) in pattern.points]):
        draw.line([(0, y), (width, y)], width=1, fill=GROUT)

    # vary the color of each dark tile and each light tile slightly.
    offset = (Pattern.scale - 1) / 2
    edge = [(width, x * pattern.scale) for x in range(1, 2**order + 1)]
    bottom = [(x * pattern.scale, height) for x in range(1, 2 ** (order + 1) + 2)]
    inside = INSIDE[0]
    outside = OUTSIDE[0]
    inner_colors = INSIDE
    outer_colors = OUTSIDE

    for x, y in pattern.points + edge + bottom:
        position = (x - offset - 1, y - offset - 1)
        if image.getpixel(position) == inside:
            color = random.choice(INSIDE)
        elif image.getpixel(position) == outside:
            color = random.choice(OUTSIDE)
        else:
            color = (0, 0, 0)
        ImageDraw.floodfill(image, position, color)

    image.show()  # XXX - Debug: show the image

    # Save the file.
    image.save(filename, image_type, quality=100)


if __name__ == "__main__":
    main()
