"""Includes properties of predefined layouts for printing. All measurements need to be specified in mm."""
import abc


class PrintLayout:
    """Abstract class that represents a generic A4 label sheet."""

    __metaclass__ = abc.ABCMeta

    a4_height = 297
    a4_width = 210

    def get_label_height(self):
        """Return height of each label in mm.

        Returns
        -------
        float
            Height of each label in mm.

        """
        height_all_labels = self.a4_height - self.top_margin - self.bottom_margin - self.inter_row * (self.num_rows - 1)
        return height_all_labels / self.num_rows

    @property
    @abc.abstractmethod
    def num_cols(self) -> int:
        """Return number of distinct labels per column."""

    @num_cols.setter
    def num_cols(self, value):
        self.num_cols = value

    @property
    @abc.abstractmethod
    def num_rows(self) -> int:
        """Return number of distinct labels per row."""

    @num_rows.setter
    def num_rows(self, value):
        self.num_rows = value

    @property
    @abc.abstractmethod
    def left_margin(self) -> float:
        """Return offset between edge of sheet and first label to the left in mm."""

    @left_margin.setter
    def left_margin(self, value):
        self.left_margin = value

    @property
    @abc.abstractmethod
    def right_margin(self) -> float:
        """Return offset between edge of sheet and first label to the right in mm."""

    @right_margin.setter
    def right_margin(self, value: float):
        """Set offset between edge of sheet and first label to the right in mm.

        Parameters
        ----------
        value : float
            Offset between edge of sheet and first label to the right in mm.

        """
        self.right_margin = value

    @property
    @abc.abstractmethod
    def top_margin(self) -> float:
        """Return offset between edge of sheet and first label to the top in mm."""

    @top_margin.setter
    def top_margin(self, value: float):
        """Set offset between edge of sheet and first label to the top in mm.

        Parameters
        ----------
        value : float
            Offset between edge of sheet and first label to the top in mm.

        """
        self.top_margin = value

    @property
    @abc.abstractmethod
    def bottom_margin(self) -> float:
        """Return offset between edge of sheet and first label to the bottom in mm."""

    @bottom_margin.setter
    def bottom_margin(self, value: float):
        """Set offset between edge of sheet and first label to the bottom in mm.

        Parameters
        ----------
        value : float
            Offset between edge of sheet and first label to the bottom in mm.

        """
        self.bottom_margin = value

    @property
    @abc.abstractmethod
    def inter_col(self) -> float:
        """Return distance between each label along the columns in mm."""

    @inter_col.setter
    def inter_col(self, value: float):
        """Set distance between each label along the columns in mm.

        Parameters
        ----------
        value : float
            Distance between each label along the columns in mm.

        """
        self.inter_col = value

    @property
    @abc.abstractmethod
    def inter_row(self) -> float:
        """Return distance between each label along the rows in mm."""

    @inter_row.setter
    def inter_row(self, value: float):
        """Set distance between each label along the rows in mm.

        Parameters
        ----------
        value : float
            Distance between each label along the rows in mm.

        """
        self.inter_row = value


class AveryZweckformJ4791Layout(PrintLayout):
    """Class that represents the layout of `AveryZweckformJ4791` label sheets."""

    num_cols = 4
    num_rows = 12
    left_margin = 9.8
    right_margin = 9.8
    top_margin = 21.2
    bottom_margin = 21.2
    inter_col = 2.5
    inter_row = 0


class CustomLayout(PrintLayout):
    """Class that represents a user-defined label sheet layout."""

    num_cols = 0
    num_rows = 0
    left_margin = 0
    right_margin = 0
    top_margin = 0
    bottom_margin = 0
    inter_col = 0
    inter_row = 0

    def __init__(
        self,
        num_cols: int,
        num_rows: int,
        left_margin: float,
        right_margin: float,
        top_margin: float,
        bottom_margin: float,
        inter_col: float,
        inter_row: float,
    ):
        """Initialize a custom layout.

        Parameters
        ----------
        num_cols : int
            Number of distinct labels per column.
        num_rows : int
            Number of distinct labels per row.
        left_margin : float
            Offset between edge of sheet and first label to the left in mm.
        right_margin : float
            Offset between edge of sheet and last label to the right in mm.
        top_margin : float
            Offset between edge of sheet and first label to the top in mm.
        bottom_margin : float
            Offset between edge of sheet and last label to the bottom in mm.
        inter_col : float
            Distance between each label along the columns in mm.
        inter_row : float
            Distance between each label along the rows in mm.

        """
        self.num_cols = num_cols
        self.num_rows = num_rows
        self.left_margin = left_margin
        self.right_margin = right_margin
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.inter_col = inter_col
        self.inter_row = inter_row
