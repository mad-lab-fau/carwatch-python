import itertools
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import click

from carwatch.labels import CustomLayout, LabelGenerator, Study, _assert_file_ending


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
            _assert_file_ending(Path(value), [".csv", ".txt"])
        except ValueError as e:
            raise click.BadParameter(str(e))
    return value


@click.command()
@click.option(
    "--study-name", required=True, prompt="Study name", type=str, help="A descriptive abbreviation for your study name."
)
@click.option(
    "--num-days", required=True, prompt="Duration of study [days]", type=int, help="The duration of your study in days."
)
@click.option(
    "--num-saliva-samples",
    required=True,
    prompt="Number of saliva samples [per day]",
    type=int,
    help="The daily number of saliva samples taken from every participant.",
)
@click.option(
    "--subject-data",
    required=True,
    prompt="Read subject IDs from file?",
    is_flag=True,
)
@click.option(
    "--subject-path",
    default=None,
    required=False,
    prompt="Path to subject data file",
    help="The path to the *.csv or *.txt file with the participant data.",
    envvar="PATHS",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    callback=validate_subject_path,
    cls=Condition,
    pos_condition="subject_data",
)
@click.option(
    "--subject-column",
    default="subject",
    required=False,
    prompt="Name of subject ID column",
    type=str,
    help="The name of the subject ID column in participants data file.",
    cls=Condition,
    pos_condition="subject_data",
)
@click.option(
    "--num-subjects",
    required=False,
    prompt="Number of participants",
    type=int,
    help="The number of participants in your study.",
    cls=Condition,
    neg_condition="subject_data",
)
@click.option(
    "--has-evening-salivette",
    required=True,
    prompt="Evening salivette?",
    is_flag=True,
    help="Whether a saliva sample is taken in the evening.",
)
@click.option(
    "--add-name",
    required=True,
    prompt="Add study name and participant number to label?",
    is_flag=True,
    help="Whether a the study name and participant id will be printed on every individual label.",
)
@click.option(
    "--has-barcode",
    required=True,
    prompt="Add barcode to label?",
    is_flag=True,
    help="Whether a barcode encoding the participant id, day of study, and number of saliva sample will be"
    " printed on every individual label.",
)
@click.option(
    "--output_dir",
    default=".",
    prompt="Output directory for labels",
    help="Directory where generated labels will be stored.",
    envvar="PATHS",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--output_name",
    default="barcodes",
    prompt="Name of label file",
    help="Name of the generated label file.",
    envvar="PATHS",
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option(
    "--custom-layout",
    required=True,
    prompt="Use custom layout instead of Avery Zweckform J4791?",
    is_flag=True,
    help="Whether a custom layout will be specified.",
)
@click.option(
    "--num_cols",
    prompt="Number of columns",
    type=int,
    help="The number of distinct labels per column",
    cls=Condition,
    pos_condition="custom_layout",
)
@click.option(
    "--num_rows",
    prompt="Number of rows",
    type=int,
    help="The number of distinct labels per row",
    cls=Condition,
    pos_condition="custom_layout",
)
@click.option(
    "--left_margin",
    prompt="Left margin",
    type=float,
    help="The offset between edge of sheet and first label to the left in mm",
    cls=Condition,
    pos_condition="custom_layout",
)
@click.option(
    "--right_margin",
    prompt="Right margin",
    type=float,
    help="The offset between edge of sheet and first label to the right in mm",
    cls=Condition,
    pos_condition="custom_layout",
)
@click.option(
    "--top_margin",
    prompt="Top margin",
    type=float,
    help="The offset between edge of sheet and first label to the top in mm",
    cls=Condition,
    pos_condition="custom_layout",
)
@click.option(
    "--bottom_margin",
    prompt="Bottom margin",
    type=float,
    help="The offset between edge of sheet and first label to the bottom in mm",
    cls=Condition,
    pos_condition="custom_layout",
)
@click.option(
    "--inter_col",
    prompt="Distance between columns",
    type=float,
    help="The distance between each label along the columns in mm",
    cls=Condition,
    pos_condition="custom_layout",
)
@click.option(
    "--inter_row",
    prompt="Distance between rows",
    type=float,
    help="The distance between each label along the rows in mm",
    cls=Condition,
    pos_condition="custom_layout",
)
def run(
    study_name: Optional[str] = None,
    num_days: Optional[int] = None,
    num_saliva_samples: Optional[int] = None,
    subject_path: Optional[str] = None,
    subject_column: Optional[str] = None,
    num_subjects: Optional[int] = None,
    has_evening_salivette: Optional[bool] = None,
    add_name: Optional[bool] = None,
    has_barcode: Optional[bool] = None,
    output_dir: Optional[str] = None,
    output_name: Optional[str] = None,
    custom_layout: Optional[bool] = None,
    **kwargs
):
    done = False

    def animate():
        """Create a loading icon while input is processed."""
        for c in itertools.cycle(["|", "/", "-", "\\"]):
            if done:
                break
            sys.stdout.write("\rloading " + c)
            sys.stdout.flush()
            time.sleep(0.1)

    t = threading.Thread(target=animate)
    t.start()

    study = Study(
        study_name=study_name,
        num_days=num_days,
        num_saliva_samples=num_saliva_samples,
        num_subjects=num_subjects,
        subject_path=subject_path,
        subject_column=subject_column,
        has_evening_salivette=has_evening_salivette,
    )
    generator = LabelGenerator(study=study, add_name=add_name, has_barcode=has_barcode)
    if custom_layout:
        layout = CustomLayout(
            num_cols=kwargs["num_cols"],
            num_rows=kwargs["num_rows"],
            left_margin=kwargs["left_margin"],
            right_margin=kwargs["right_margin"],
            top_margin=kwargs["top_margin"],
            bottom_margin=kwargs["bottom_margin"],
            inter_col=kwargs["inter_col"],
            inter_row=kwargs["inter_row"],
        )
        generator.generate(output_dir=output_dir, output_name=output_name, layout=layout)
    else:
        generator.generate(output_dir=output_dir, output_name=output_name)
    done = True


if __name__ == "__main__":
    run()
