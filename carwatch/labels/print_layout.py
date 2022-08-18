"""Includes properties of predefined layouts for printing"""
import abc


class PrintLayout:
    __metaclass__ = abc.ABCMeta

    @property
    @abc.abstractmethod
    def num_cols(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def num_rows(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def col_width(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def row_height(self) -> int:
        pass


class AveryZweckformJ4791Layout(PrintLayout):
    num_cols = 4
    num_rows = 12
    col_width = 45.7
    row_height = 21.2
