import itertools
import sys
import threading
import time
from typing import Optional, Union, Sequence

import click

from carwatch.labels import CustomLayout, LabelGenerator
from carwatch.qr_codes import QrCodeGenerator
from carwatch.utils import Study, validate_subject_path, Condition, validate_mail_input, validate_saliva_distances


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
    "--saliva_start_id",
    required=True,
    default=0,
    prompt="Should saliva IDs start at 0 or at 1 (i.e., S0 vs. S1)?",
    type=click.IntRange(0, 1),
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
    "--has-subject-prefix",
    required=True,
    prompt="Add prefix to participant number (e.g., 'VP_')?",
    is_flag=True,
)
@click.option(
    "--subject-prefix",
    default="VP_",
    required=False,
    prompt="Subject prefix",
    type=str,
    help="Specification of subject prefix.",
    cls=Condition,
    pos_condition="has_subject_prefix",
)
@click.option(
    "--has-evening-salivette",
    required=True,
    prompt="Evening salivette?",
    is_flag=True,
    help="Whether a saliva sample is taken in the evening.",
)
@click.option(
    "--generate-barcode",
    required=True,
    prompt="Generate printable labels for study?",
    is_flag=True,
    help="Whether a PDF with barcodes encoding the information for individual saliva samples should be generated.",
)
@click.option(
    "--add-name",
    prompt="Add study name and participant number to label?",
    is_flag=True,
    help="Whether a the study name and participant id will be printed on every individual label.",
    cls=Condition,
    pos_condition="generate_barcode",
)
@click.option(
    "--has-barcode",
    prompt="Add barcode to label?",
    is_flag=True,
    help="Whether a barcode encoding the participant id, day of study, and number of saliva sample will be"
         " printed on every individual label.",
    cls=Condition,
    pos_condition="generate_barcode",
)
@click.option(
    "--custom-layout",
    prompt="Use custom layout instead of Avery Zweckform J4791?",
    is_flag=True,
    help="Whether a custom layout will be specified.",
    cls=Condition,
    pos_condition="generate_barcode",
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
@click.option(
    "--generate-qr",
    required=True,
    prompt="Use CAR Watch app for study?",
    is_flag=True,
    help="Whether a qr code encoding the study data for configuring the CAR watch app should be generated.",
)
@click.option(
    "--output_dir",
    default=".",
    prompt="Output directory for generated files",
    help="Directory where generated files will be stored.",
    envvar="PATHS",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--output_name_label",
    default="barcodes",
    prompt="Name of label file",
    help="Name of the generated label file.",
    envvar="PATHS",
    type=click.Path(file_okay=True, dir_okay=False),
    cls=Condition,
    pos_condition="generate_barcode",
)
@click.option(
    "--output_name_qr",
    default="qr_code",
    prompt="Name of QR code file",
    help="Name of the generated QR code file.",
    envvar="PATHS",
    type=click.Path(file_okay=True, dir_okay=False),
    cls=Condition,
    pos_condition="generate_qr",
)
@click.option(
    "--saliva-distances",
    default="15",
    required=False,
    prompt="Please specify duration between all saliva samples in minutes"
           " (as number when constant, as comma-separated when varying from sample to sample)",
    type=str,
    help="The duration between saliva samples in minutes.",
    callback=validate_saliva_distances,
    cls=Condition,
    pos_condition="generate_qr",
)
@click.option(
    "--contact-email",
    required=False,
    prompt="Contact E-Mail Address that should receive CAR Watch app timestamps",
    type=str,
    help="The E-Mail Address that will be used as default when sharing data from CAR Watch app.",
    callback=validate_mail_input,
    cls=Condition,
    pos_condition="generate_qr",
)
def run(
        study_name: Optional[str] = None,
        num_days: Optional[int] = None,
        num_saliva_samples: Optional[int] = None,
        saliva_start_id: Optional[int] = None,
        subject_path: Optional[str] = None,
        subject_column: Optional[str] = None,
        num_subjects: Optional[int] = None,
        has_subject_prefix: Optional[bool] = None,
        subject_prefix: Optional[str] = None,
        has_evening_salivette: Optional[bool] = None,
        add_name: Optional[bool] = None,
        has_barcode: Optional[bool] = None,
        output_dir: Optional[str] = None,
        generate_barcode: Optional[bool] = None,
        generate_qr: Optional[bool] = None,
        output_name_label: Optional[str] = None,
        output_name_qr: Optional[str] = None,
        custom_layout: Optional[bool] = None,
        saliva_distances: Optional[str] = None,
        contact_email: Optional[str] = None,
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

    if not generate_qr and not generate_barcode:
        done = True
        raise click.UsageError("Nothing to do, no output generated.")

    start_saliva_from_zero = True if saliva_start_id == 0 else False

    study = Study(
        study_name=study_name,
        num_days=num_days,
        num_saliva_samples=num_saliva_samples,
        start_saliva_from_zero=start_saliva_from_zero,
        num_subjects=num_subjects,
        subject_path=subject_path,
        subject_column=subject_column,
        subject_prefix=subject_prefix,
        has_evening_salivette=has_evening_salivette,
    )

    if generate_barcode:
        _generate_barcode(study, add_name, has_barcode, custom_layout, output_dir, output_name_label, **kwargs)
    if generate_qr:
        try:
            _generate_qr_code(study, saliva_distances, contact_email, output_dir, output_name_qr)
        except ValueError as e:
            done = True
            raise click.BadParameter(str(e))

    done = True


def _generate_barcode(study, add_name, has_barcode, custom_layout, output_dir, output_name_label, **kwargs):
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
        generator.generate(output_dir=output_dir, output_name=output_name_label, layout=layout)
    else:
        generator.generate(output_dir=output_dir, output_name=output_name_label)


def _generate_qr_code(study, saliva_distances, contact_email, output_dir, output_name_qr):
    saliva_distances = _parse_saliva_distances(saliva_distances, study.num_saliva_samples)
    generator = QrCodeGenerator(study=study, saliva_distances=saliva_distances, contact_email=contact_email)
    generator.generate(output_dir=output_dir, output_name=output_name_qr)


def _parse_saliva_distances(saliva_distances: Union[Sequence[str], str], num_saliva_samples: int) -> Sequence[int]:
    saliva_distances = saliva_distances.replace(" ", "")  # trim spaces
    # list of int
    if "," in saliva_distances:
        saliva_distances = [eval(dist) for dist in saliva_distances.split(",")]
        return saliva_distances
    else:
        return [int(saliva_distances)] * (num_saliva_samples - 1)


if __name__ == "__main__":
    run()
