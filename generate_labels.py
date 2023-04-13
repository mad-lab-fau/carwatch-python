"""Main script for the CLI interface of the carwatch package."""
import itertools
import sys
import threading
import time
from typing import Optional, Sequence, Union

import click

from carwatch.labels import LabelGenerator
from carwatch.labels.print_layout import CustomLayout
from carwatch.qr_codes import QrCodeGenerator
from carwatch.utils import Condition, Study, validate_mail_input, validate_saliva_distances, validate_subject_path
from carwatch.utils.click_helper import NumericChoice, get_file_name

CAR_STUDY = 1
LAB_STUDY = 2
OTHER_STUDY = 3
STUDY_TYPES = [CAR_STUDY, LAB_STUDY, OTHER_STUDY]
EVENING_OPTION = {CAR_STUDY: True, LAB_STUDY: False, OTHER_STUDY: True}
APP_OPTION = {CAR_STUDY: True, LAB_STUDY: False, OTHER_STUDY: True}

SEPARATOR = f"{'-' * 30}\n"
DEFAULT_BARCODE_FILE_SUFFIX = "_barcodes"
DEFAULT_QR_FILE_SUFFIX = "_qr_code"


@click.command()
@click.option(
    "--study-name", required=True, prompt="Study name", type=str, help="A descriptive abbreviation for your study name."
)
@click.option(
    "--num-days", required=True, prompt="Duration of study [days]", type=int, help="The duration of your study in days."
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
    prompt="Add prefix to participant number (e.g., 'VP_')?",
    is_flag=True,
    cls=Condition,
    neg_condition="subject_path",
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
    "--num-samples",
    required=True,
    prompt="Number of biomarker samples [per day]",
    type=int,
    help="The daily number of biomarker samples taken from every participant.",
)
@click.option(
    "--sample_prefix",
    required=True,
    default="S",
    prompt="Prefix for your type of biomarker (e.g., S for saliva)",
    type=str,
    help="The prefix for the biomarker type of the collected samples.",
)
@click.option(
    "--sample_start_id",
    required=True,
    default=0,
    prompt="Should biomarker IDs start at 0 or at 1 (i.e., S0 vs. S1)?",
    type=click.IntRange(0, 1),
)
@click.option(
    "--study_type",
    required=True,
    default=CAR_STUDY,
    prompt="Type of study? (1 for CAR study, 2 for Lab-based study, 3 for Other)?",
    type=click.IntRange(1, len(STUDY_TYPES)),
)
@click.option(
    "--has-evening-sample",
    prompt="Evening sample taken?",
    is_flag=True,
    help="Whether a biomarker sample is taken in the evening.",
    cls=NumericChoice,
    chosen_number="study_type",
    option_map=EVENING_OPTION,
)
@click.option(
    "--generate-barcode",
    required=True,
    prompt=f"{SEPARATOR}Generate printable labels for study?",
    is_flag=True,
    help="Whether a PDF with barcodes encoding the information for individual biomarker samples should be generated.",
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
    help="Whether a barcode encoding the participant id, day of study, and number of biomarker sample will be"
         " printed on every individual label.",
    cls=Condition,
    pos_condition="generate_barcode",
)
@click.option(
    "--default-layout",
    prompt="Use Avery Zweckform J4791 as default layout?",
    is_flag=True,
    default=True,
    help="Whether the default layout will be used specified.",
    cls=Condition,
    pos_condition="generate_barcode",
)
@click.option(
    "--num_cols",
    prompt="Number of columns",
    type=int,
    help="The number of distinct labels per column",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--num_rows",
    prompt="Number of rows",
    type=int,
    help="The number of distinct labels per row",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--left_margin",
    prompt="Left margin",
    type=float,
    help="The offset between edge of sheet and first label to the left in mm",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--right_margin",
    prompt="Right margin",
    type=float,
    help="The offset between edge of sheet and first label to the right in mm",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--top_margin",
    prompt="Top margin",
    type=float,
    help="The offset between edge of sheet and first label to the top in mm",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--bottom_margin",
    prompt="Bottom margin",
    type=float,
    help="The offset between edge of sheet and first label to the bottom in mm",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--inter_col",
    prompt="Distance between columns",
    type=float,
    help="The distance between each label along the columns in mm",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--inter_row",
    prompt="Distance between rows",
    type=float,
    help="The distance between each label along the rows in mm",
    cls=Condition,
    neg_condition="default_layout",
)
@click.option(
    "--output_name_label",
    default=lambda: get_file_name(DEFAULT_BARCODE_FILE_SUFFIX),
    prompt="Name of label file",
    help="Name of the generated label file.",
    envvar="PATHS",
    type=click.Path(file_okay=True, dir_okay=False),
    cls=Condition,
    pos_condition="generate_barcode",
)
@click.option(
    "--generate-qr",
    prompt=f"{SEPARATOR}Use CAR Watch app for study?",
    is_flag=True,
    cls=NumericChoice,
    chosen_number="study_type",
    option_map=APP_OPTION,
    help="Whether a qr code encoding the study data for configuring the CAR watch app should be generated.",
)
@click.option(
    "--output_name_qr",
    default=lambda: get_file_name(DEFAULT_QR_FILE_SUFFIX),
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
           " (as number when constant, as comma-separated list when varying from sample to sample)",
    type=str,
    help="The duration between saliva samples in minutes.",
    callback=validate_saliva_distances,
    cls=Condition,
    pos_condition="generate_qr",
)
@click.option(
    "--contact-email",
    required=False,
    prompt="Contact E-Mail Address that should receive CARWatch app timestamps",
    type=str,
    help="The E-Mail Address that will be used as default when sharing data from CARWatch app.",
    callback=validate_mail_input,
    cls=Condition,
    pos_condition="generate_qr",
)
@click.option(
    "--check-duplicates",
    prompt="Check for duplicate barcodes in app?",
    default=False,
    is_flag=True,
    cls=Condition,
    pos_condition="generate_qr",
    help="Whether the CARWatch app will check for every barcode, if it was scanned before.",
)
@click.option(
    "--enable-manual-scan",
    prompt="Enable manual scanning in app?",
    default=False,
    is_flag=True,
    cls=Condition,
    pos_condition="generate_qr",
    help="Whether the CARWatch app will allow manual scanning of sample barcodes apart from timed alarms.",
)
@click.option(
    "--output_dir",
    default=".",
    prompt="Output directory for generated files",
    help="Directory where generated files will be stored.",
    envvar="PATHS",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def run(
        sample_prefix: Optional[str] = None,
        study_name: Optional[str] = None,
        num_days: Optional[int] = None,
        num_samples: Optional[int] = None,
        sample_start_id: Optional[int] = None,
        subject_path: Optional[str] = None,
        subject_column: Optional[str] = None,
        num_subjects: Optional[int] = None,
        has_subject_prefix: Optional[bool] = None,  # pylint: disable=unused-argument
        subject_prefix: Optional[str] = None,
        has_evening_sample: Optional[bool] = None,
        add_name: Optional[bool] = None,
        has_barcode: Optional[bool] = None,
        generate_barcode: Optional[bool] = None,
        generate_qr: Optional[bool] = None,
        output_name_label: Optional[str] = None,
        output_name_qr: Optional[str] = None,
        default_layout: Optional[bool] = None,
        saliva_distances: Optional[str] = None,
        contact_email: Optional[str] = None,
        check_duplicates: Optional[bool] = None,
        enable_manual_scan: Optional[bool] = None,
        output_dir: Optional[str] = None,
        **kwargs,
):
    """Generate barcode labels and QR codes for CAR study.

    Parameters
    ----------
    sample_prefix : str, optional
        Prefix for sample barcodes. Default: None
    study_name : str, optional
        Name of the study. Default: None
    num_days : int, optional
        Number of days of the study. Default: None
    num_samples : int, optional
        Number of samples per day. Default: None
    sample_start_id : int, optional
        ID of the first sample. Default: None
    subject_path : str, optional
        Path to the subject file. Default: None
    subject_column : str, optional
        Name of the column in the subject file that contains the subject IDs. Default: None
    num_subjects : int, optional
        Number of subjects. Default: None
    has_subject_prefix : bool, optional
        Whether the subject IDs have a prefix. Default: None
    subject_prefix : str, optional
        Prefix for subject IDs. Default: None
    has_evening_sample : bool, optional
        Whether the study has an evening sample. Default: None
    add_name : bool, optional
        Whether the subject name should be added to the label. Default: None
    has_barcode : bool, optional
        Whether the study has a barcode. Default: None
    output_dir : str, optional
        Path to the output directory. Default: None
    generate_barcode : bool, optional
        Whether a barcode label should be generated. Default: None
    generate_qr : bool, optional
        Whether a QR code should be generated. Default: None
    output_name_label : str, optional
        Name of the generated barcode label file. Default: None
    output_name_qr : str, optional
        Name of the generated QR code file. Default: None
    default_layout : bool, optional
        Whether the default layout (Avery Zweckform J4791) should be used. Default: None
    saliva_distances : str, optional
        The duration between saliva samples in minutes. Default: None
    contact_email : str, optional
        The E-Mail Address that will be used as default when sharing data from CARWatch app. Default: None
    check_duplicates : bool, optional
        Whether the CARWatch app will check for every barcode, if it was scanned before. Default: None
    enable_manual_scan : bool, optional
        Whether the CARWatch app will allow manual scanning of sample barcodes apart from timed alarms. Default: None
    **kwargs : dict
        Additional keyword arguments.

    """
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

    start_sample_from_zero = sample_start_id == 0

    study = Study(
        study_name=study_name,
        num_days=num_days,
        num_samples=num_samples,
        start_sample_from_zero=start_sample_from_zero,
        num_subjects=num_subjects,
        subject_path=subject_path,
        subject_column=subject_column,
        subject_prefix=subject_prefix,
        has_evening_sample=has_evening_sample,
    )

    if generate_barcode:
        _generate_barcode(
            study, add_name, has_barcode, sample_prefix, default_layout, output_dir, output_name_label, **kwargs
        )
    if generate_qr:
        try:
            _generate_qr_code(
                study, saliva_distances, contact_email, check_duplicates, enable_manual_scan, output_dir, output_name_qr
            )
        except ValueError as e:
            done = True
            raise click.BadParameter(str(e))

    done = True


def _generate_barcode(
        study, add_name, has_barcode, sample_prefix, default_layout, output_dir, output_name_label, **kwargs
):
    generator = LabelGenerator(study=study, add_name=add_name, has_barcode=has_barcode, sample_prefix=sample_prefix)
    if not default_layout:
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


def _generate_qr_code(
        study, saliva_distances, contact_email, check_duplicates, enable_manual_scan, output_dir, output_name_qr
):
    saliva_distances = _parse_saliva_distances(saliva_distances)
    generator = QrCodeGenerator(
        study=study,
        saliva_distances=saliva_distances,
        contact_email=contact_email,
        check_duplicates=check_duplicates,
        enable_manual_scan=enable_manual_scan,
    )
    generator.generate(output_dir=output_dir, output_name=output_name_qr)


def _parse_saliva_distances(saliva_distances: Union[Sequence[str], str]) -> Union[int, Sequence[int]]:
    saliva_distances = saliva_distances.replace(" ", "")  # trim spaces
    # list of int
    if "," in saliva_distances:
        saliva_distances = [eval(dist) for dist in saliva_distances.split(",")]  # pylint: disable=eval-used
        return saliva_distances

    return int(saliva_distances)


if __name__ == "__main__":
    run()
