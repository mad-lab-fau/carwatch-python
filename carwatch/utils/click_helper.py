from pathlib import Path

import click
import re

from carwatch.utils import assert_file_ending


class Condition(click.Option):
    """Helper class that displays options as prompt depending on flag options previously set by user."""

    def __init__(self, *args, **kwargs):
        """Display options as prompt depending on flag options previously set by user.

        To invoke this feature for an option, specify ``cls=Condition`` and ``pos_condition="conditional_option"``
        for positive relations and ``neg_condition="conditional_option"`` for negative relations.
        Note that ``conditional_option`` need to be either a flag or a bool.

        Parameters
        ----------
        condition: str
            name of a previously prompted variable that decides whether the current option is needed or not
        is_positive: bool
            ``True`` when the relation between current and conditional variable are positive,
            i.e., prompt for current option is shown when ``condition`` is ``True``
            ``False`` when the current option should be hidden if ``condition`` is ``True``

        """
        if "pos_condition" in kwargs:
            self.condition = kwargs.pop("pos_condition")
            self.is_positive = True
        else:
            self.condition = kwargs.pop("neg_condition")
            self.is_positive = False
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        is_condition = ctx.params[self.condition]

        if not is_condition:
            if self.is_positive:
                self.prompt = None
            else:
                self.required = True

        if is_condition:
            if not self.is_positive:
                self.prompt = None
            else:
                self.required = True

        return super().handle_parse_result(ctx, opts, args)


def validate_subject_path(ctx, param, value):  # pylint:disable=unused-argument
    if value:
        try:
            assert_file_ending(Path(value), [".csv", ".txt"])
        except ValueError as e:
            raise click.BadParameter(str(e))
    return value


def validate_mail_input(ctx, param, value):  # pylint:disable=unused-argument
    if value:
        email_regex = r"[^@]+@[^@]+\.[^@]+"  # pattern <...>@<...>.<...>
        if not re.fullmatch(email_regex, value):
            raise click.BadParameter(f"{value} is not an email address!")
    return value


def validate_saliva_distances(ctx, param, value):  # pylint:disable=unused-argument
    if value:
        value = value.replace(" ", "")  # trim spaces
        if "," in value:
            distances = value.split(",")
            for dist in distances:
                if not dist.isdigit():
                    raise click.BadParameter(f"Saliva distances need to be comma-separated integers!")
        else:
            if not value.isdigit():
                raise click.BadParameter(f"Saliva distance needs to be an integer!")
    return value
