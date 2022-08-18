import click

from carwatch.labels import LabelGenerator, Study


@click.command()
@click.option(
    "--study-name", required=True, prompt="Study name", type=str, help="A descriptive abbreviation for your study name."
)
@click.option(
    "--num-days", required=True, prompt="Duration of study [days]", type=int, help="The duration of your study in days."
)
@click.option(
    "--num-subjects",
    required=True,
    prompt="Number of participants",
    type=int,
    help="The number of participants in your study.",
)
@click.option(
    "--num-saliva-samples",
    required=True,
    prompt="Number of saliva samples [per day]",
    type=int,
    help="The daily number of saliva samples taken from every participant.",
)
@click.option(
    "--has-evening-salivette",
    required=True,
    prompt="Evening salivette? [yes/no]",
    type=bool,
    help="Whether a saliva sample is taken in the evening.",
)
@click.option(
    "--add-name",
    required=True,
    prompt="Add study name and participant number to label? [yes/no]",
    type=bool,
    help="Whether a the study name and participant id will be printed on every individual label.",
)
@click.option(
    "--has-barcode",
    required=True,
    prompt="Add barcode to label? [yes/no]",
    type=bool,
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
    type=click.Path(file_okay=True, dir_okay=False),
)
def run(
    study_name,
    num_days,
    num_subjects,
    num_saliva_samples,
    has_evening_salivette,
    add_name,
    has_barcode,
    output_dir,
    output_name,
):
    study = Study(
        study_name=study_name,
        num_days=num_days,
        num_subjects=num_subjects,
        num_saliva_samples=num_saliva_samples,
        has_evening_salivette=has_evening_salivette,
    )
    generator = LabelGenerator(study=study, add_name=add_name, has_barcode=has_barcode)
    generator.generate(output_dir=output_dir, output_name=output_name)


if __name__ == "__main__":
    run()
