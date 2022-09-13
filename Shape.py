import copy
from math import sqrt
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
import random

DEFAULT_LINE_COLOR = QtGui.QColor(0, 255, 0, 128)  # bf hovering
DEFAULT_FILL_COLOR = QtGui.QColor(0, 255, 0, 128)  # hovering
DEFAULT_SELECT_LINE_COLOR = QtGui.QColor(255, 255, 255)  # selected
DEFAULT_SELECT_FILL_COLOR = QtGui.QColor(0, 255, 0, 155)  # selected
DEFAULT_VERTEX_FILL_COLOR = QtGui.QColor(0, 255, 0, 255)  # hovering
DEFAULT_HVERTEX_FILL_COLOR = QtGui.QColor(255, 255, 255, 255)  # hovering


class Shape(object):
    P_SQUARE = 0
    P_ROUND = 1

    # Flag for the handles if dragging
    MOVE_VERTEX = 0

    # Flag for all other handles
    NEAR_VERTEX = 1

    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR  #highlight
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    def __init__(self, label=None, line_color=None, flags=None, group_id=None):
        self.label = label
        self.group_id = group_id
        self.points = list()
        self.fill = False
        self.selected = False
        self.flags = flags
        self.other_data = dict()

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
            self.NEAR_VERTEX: (4, self.P_ROUND)
        }

        self._closed = False

        if line_color is not None:
            self.line_color = line_color

        self.shape_type = "rectangle"

    def close(self):
        self._closed = True

    def setOpen(self):
        self._closed = False

    def addPoint(self, point):  # polygon
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def insertPoint(self, index, point):
        self.points.insert(index, point)

    def removePoint(self, index):
        self.points.pop(index)

    def isClosed(self):
        return self._closed

    def getRectFromLine(self, pt1, pt2):
        x1, y1 = pt1.x(), pt1.y()
        x2, y2 = pt2.x(), pt2.y()
        return QtCore.QRectF(x1, y1, x2-x1, y2-y1)

    def drawVertex(self, path, index):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[index]
        if index == self._highlightIndex:  # highligtVertex 함수로 설정. default = None
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size  # NEAR_VERTEX : 4  MOVE_VERTEX : 1.5
        if self._highlightIndex is not None:
            self._vertex_fill_color = self.hvertex_fill_color
        else:
            self._vertex_fill_color = self.vertex_fill_color

        if shape == self.P_SQUARE:
            path.addRect(point.x() - d/2, point.y() - d/2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(QtCore.QPointF(point), d/2.0, d/2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        min_distance = float('inf')
        min_i = None
        for i, p in enumerate(self.points):
            distance = self.distance(p-point)
            if distance <= epsilon and distance < min_distance:
                min_distance = distance
                min_i = i
        return min_i

    def nearestEdge(self, point, epsilon):
        min_distance = float('inf')
        post_i = None
        for i in range(len(self.points)):
            line = [self.points[i-1], self.points[i]]
            distance = self.distancetoline(point, line)
            if distance <= epsilon and distance < min_distance:
                min_distance = distance
                post_i = i
        return post_i

    def paint(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.line_color

            pen = QtGui.QPen(color)
            pen.setWidth(max(1, int(round(2.0/self.scale))))
            painter.setPen(pen)

        line_path = QtGui.QPainterPath()
        vrtx_path = QtGui.QPainterPath()

        # draw rectangle and vertex
        assert len(self.points) in [1, 2], f"{len(self.points)}"
        if len(self.points) == 2:
            rectangle = self.getRectFromLine(*self.points)  # 언패킹
            line_path.addRect(rectangle)  # path에 QRectF 객체 추가
        for i in range(len(self.points)):
            self.drawVertex(vrtx_path, i)

        painter.drawPath(line_path)
        painter.drawPath(vrtx_path)
        painter.fillPath(vrtx_path, self._vertex_fill_color)

        #  fill rectangle
        if self.fill:  # default = False
            color = self.select_fill_color if self.selected else self.fill_color
            painter.fillPath(line_path, color)

    #  return bool whether path contains given point
    def containsPoint(self, point):
        return self.makePath().contains(QtCore.QPointF(point))

    # return rectangle path made by points
    def makePath(self):
        path = QtGui.QPainterPath()
        if len(self.points) == 2:
            rectangle = self.getRectFromLine(*self.points)
            path.addRect(rectangle)
        return path

    #  QPaintPath.boundingRect()
    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, index, offset):
        self.points[index] = self.points[index] + offset

    def highlightVertex(self, index, action):
        self._highlightIndex = index
        self._highlightMode = action  # MOVE_VERTEX or NEAR_VERTEX

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        return copy.deepcopy(self)

    def distance(self, p):
        return sqrt(p.x() * p.x() + p.y() * p.y())

    def distancetoline(self, point, line):
        p1, p2 = line
        p1 = np.array([p1.x(), p1.y()])
        p2 = np.array([p2.x(), p2.y()])
        p3 = np.array([point.x(), point.y()])
        if np.dot((p3-p1), (p2-p1)) < 0:
            return np.linalg.norm(p3-p1)
        if np.dot((p3-p2), (p1-p2)) < 0:
            return np.linalg.norm(p3-p2)
        if np.linalg.norm(p2-p1) == 0:
            return 0
        return np.linalg.norm(np.cross(p2-p1, p1-p3)) / np.linalg.norm(p2-p1)

    # def change_shape_color(self):
    #     r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    #     self.line_color = QtGui.QColor(r, g, b, 128)
    #     self.select_line_color = QtGui.QColor(r, g, b, 128)
    #     self.fill_color = QtGui.QColor(r, g, b, 128)
    #     self.vertex_fill_color = QtGui.QColor(r, g, b, 128)

    def __len__(self):
        return len(self.points)

    def __getitem__(self, item):
        return self.points[item]

    def __setitem__(self, key, value):
        self.points[key] = value
