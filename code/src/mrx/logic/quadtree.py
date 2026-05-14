
class QuadTreeNode:
  def __init__(self, boundary, depth = 0):
    self.boundary = boundary
    self.depth = depth

    self.nw = None
    self.ne = None
    self.sw = None
    self.se = None

  def subdivide(self):
    x_mid = self.boundary.mid_x()
    y_mid = self.boundary.mid_y()

    x_min = self.boundary.x_min
    x_max = self.boundary.x_max
    y_min = self.boundary.y_min
    y_max = self.boundary.y_max

    self.nw = QuadTreeNode(
        Rectangle(x_min, y_mid, x_mid, y_max),
        self.depth + 1
    )

    self.ne = QuadTreeNode(
        Rectangle(x_mid, y_mid, x_max, y_max),
        self.depth + 1
    )

    self.sw = QuadTreeNode(
        Rectangle(x_min, y_min, x_mid, y_mid),
        self.depth + 1
    )

    self.se = QuadTreeNode(
        Rectangle(x_mid, y_min, x_max, y_mid),
        self.depth + 1
    )

  def get_quadrant(self, vertical, horizontal):

    if self.nw is None:
      self.subdivide()

    if vertical == "top" and horizontal == "left":
      return self.nw

    if vertical == "top" and horizontal == "right":
      return self.ne

    if vertical == "bottom" and horizontal == "left":
      return self.sw

    if vertical == "bottom" and horizontal == "right":
      return self.se

    raise ValueError("invalid quadrant")


class Rectangle:

  def __init__(self,x_min ,y_min , x_max ,y_max):
    self.x_min = x_min
    self.y_min = y_min
    self.x_max = x_max
    self.y_max = y_max

  def mid_x(self):
    return (self.x_min + self.x_max) / 2

  def mid_y(self):
    return (self.y_min + self.y_max) / 2

  def __str__(self):
    return (f"Rectangle("
            f""f"x:[{self.x_min}, {self.x_max}], "
            f"y:[{self.y_min}, {self.y_max}])"
            )
