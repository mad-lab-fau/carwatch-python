"""Includes properties of predefined layouts for printing. All measurements need to be specified in mm."""
import abc
from abc import ABC


class PrintLayout:
    __metaclass__ = abc.ABCMeta

    a4_height = 297
    a4_width = 210

    def get_label_height(self):
        height_all_labels = self.a4_height - self.top_margin - self.bottom_margin - self.inter_row * (self.num_rows - 1)
        return height_all_labels / self.num_rows

    @property
    @abc.abstractmethod
    def num_cols(self) -> int:
        pass

    @num_cols.setter
    def num_cols(self, value):
        self.num_cols = value

    @property
    @abc.abstractmethod
    def num_rows(self) -> int:
        pass

    @num_rows.setter
    def num_rows(self, value):
        self.num_rows = value

    @property
    @abc.abstractmethod
    def left_margin(self) -> float:
        pass

    @left_margin.setter
    def left_margin(self, value):
        self.left_margin = value

    @property
    @abc.abstractmethod
    def right_margin(self) -> float:
        pass

    @right_margin.setter
    def right_margin(self, value):
        self.right_margin = value

    @property
    @abc.abstractmethod
    def top_margin(self) -> float:
        pass

    @top_margin.setter
    def top_margin(self, value):
        self.top_margin = value

    @property
    @abc.abstractmethod
    def bottom_margin(self) -> float:
        pass

    @bottom_margin.setter
    def bottom_margin(self, value):
        self.bottom_margin = value

    @property
    @abc.abstractmethod
    def inter_col(self) -> float:
        pass

    @inter_col.setter
    def inter_col(self, value):
        self.inter_col = value

    @property
    @abc.abstractmethod
    def inter_row(self) -> float:
        pass

    @inter_row.setter
    def inter_row(self, value):
        self.inter_row = value


class AveryZweckformJ4791Layout(PrintLayout):
    num_cols = 4
    num_rows = 12
    left_margin = 9.8
    right_margin = 9.8
    top_margin = 21.2
    bottom_margin = 21.2
    inter_col = 2.5
    inter_row = 0


class CustomLayout(PrintLayout):
    num_cols = 0
    num_rows = 0
    left_margin = 0
    right_margin = 0
    top_margin = 0
    bottom_margin = 0
    inter_col = 0
    inter_row = 0

    def __init__(self, num_cols: int, num_rows: int, left_margin: float, right_margin: float, top_margin: float,
                 bottom_margin: float, inter_col: float, inter_row: float):
        self.num_cols = num_cols
        self.num_rows = num_rows
        self.left_margin = left_margin
        self.right_margin = right_margin
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.inter_col = inter_col
        self.inter_row = inter_row
