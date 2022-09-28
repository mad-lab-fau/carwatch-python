import click
from carwatch.labels import LabelGenerator, Study, _assert_file_ending


class Condition(click.Option):
    """Helper class that displays options as prompt depending on flag options previously set by user."""

    def __init__(self, *args, **kwargs):
        """
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
        if "pos_condition" in kwargs.keys():
            self.condition = kwargs.pop('pos_condition')
            self.is_positive = True
        else:
            self.condition = kwargs.pop('neg_condition')
            self.is_positive = False
        super(Condition, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        is_condition = ctx.params[self.condition]

        if not is_condition and self.is_positive:
            self.prompt = None
        if is_condition and not self.is_positive:
            self.prompt = None

        return super(Condition, self).handle_parse_result(
            ctx, opts, args)


def validate_subject_path(ctx, param, value):
    if value:
        try:
            _assert_file_ending(Path(value), [".csv", ".txt"])
        except ValueError as e:
            raise click.BadParameter(str(e))


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
    help="The daily number of saliva samples taken from every participant."
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
    pos_condition="subject_data"
)
@click.option(
    "--subject-column",
    default="subject",
    required=False,
    prompt="Name of subject ID column",
    type=str,
    help="The name of the subject ID column in participants data file.",
    cls=Condition,
    pos_condition="subject_data"
)
@click.option(
    "--num-subjects",
    required=False,
    prompt="Number of participants",
    type=int,
    help="The number of participants in your study.",
    cls=Condition,
    neg_condition="subject_data"
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
def run(
        study_name,
        num_days,
        num_saliva_samples,
        subject_data,
        subject_path,
        subject_column,
        num_subjects,
        has_evening_salivette,
        add_name,
        has_barcode,
        output_dir,
        output_name,
):
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
    generator.generate(output_dir=output_dir, output_name=output_name)


if __name__ == "__main__":
    run()
