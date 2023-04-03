# CARWatch

ARWatch is a framework to support objective and low-cost assessment of biomarker samples.
It consists of an [Android app](https://github.com/mad-lab-fau/carwatch-app) that schedules sampling times and tracks
them automatically by scanning a barcode on the respective tube.
Furthermore, within this package, it provides tools to prepare studies, and process the data recorded in the app.
Preparation steps include generating unique barcodes for sampling tubes and a QR-Code for configuring the smartphone
app, all based on your individual study setup.

## Features

* User-friendly command-line interface
* Customize study properties to your needs
* Generate barcodes for sampling swabs
* Customize barcodes to fit your printable labels
* Generate QR-Code for [CARWatch App](https://github.com/mad-lab-fau/carwatch-app)
* Set up your sampling schedule
* Analyze the data recorded by the [CARWatch App](https://github.com/mad-lab-fau/carwatch-app)

## Installation

Make sure you have poetry and python 3.8 or higher installed on your system.
Then run the following commands in the terminal:

```
git clone https://github.com/mad-lab-fau/carwatch.git
cd carwatch
poetry install
```

## Usage

CarWatch can be used both programmatically and with the provided command line interface (CLI).

The core functionalities of the CARWatch package are

* creating a PDF-File of printable sampling swab labels (Preparation),
* creating a QR-Code for configuring the [CARWatch App](https://github.com/mad-lab-fau/carwatch-app) (Preparation),
* and extracting the sampling timestamps for the CARWAtch App's records (Postprocessing).

### Programmatic Usage

For the preparation steps, the study details can be specified using the `Study` class. Subject names can also be parsed
from a *.csv-File, when the path to it is specified as `subject_path`, and the corresponding column as `aubject_column`.
Some basic examples are given below. For more information about the available parameters, please refer to the
documentation of the mentioned classes.

#### Barcode Generation Example

For generating barcodes, the `LabelGenerator` class can be used, receiving the `Study` object as a parameter. Your
specific printing label layout can be specified using the `CustomLayout` class. Per default, the [
_AveryZweckformJ4791_](https://www.avery-zweckform.com/vorlage-j4791) layout is used.
To start the PDF generation, the `generate` method of the `LabelGenerator` class can be called. The output PDF can be
found in the specified `output_dir` directory, per default the current working directory.

```python
from carwatch.utils import Study
from carwatch.labels import CustomLayout, LabelGenerator

study = Study(
    study_name="ExampleStudy",
    num_days=3,
    num_subjects=15,
    num_samples=5,
    subject_prefix="VP_",
    has_evening_sample=True,
    start_sample_from_zero=True,
)
generator = LabelGenerator(study=study, add_name=True, has_barcode=True)
layout = CustomLayout(
    num_cols=3,
    num_rows=4,
    left_margin=3,
    right_margin=3,
    top_margin=2,
    bottom_margin=2,
    inter_col=0.2,
    inter_row=0.5,
)
generator.generate(output_dir=".", debug=True, layout=layout)
```

#### QR-Code Generation Example

For generating the QR-Code, the `QrCodeGenerator` class can be used, again receiving the `Study` object as a parameter.
The `saliva_distances` parameter specifies the desired distances between saliva samples in minutes. The output QR-Code
can be found as *.png-Image in the specified `output_dir` directory, per default the current working directory.

```python
from carwatch.labels import CustomLayout, LabelGenerator
from carwatch.qr_codes import QrCodeGenerator
from carwatch.utils import Study

if __name__ == "__main__":
    study = Study(
        study_name="ExampleStudy",
        num_days=3,
        num_subjects=15,
        num_samples=5,
        subject_prefix="VP_",
        has_evening_sample=True,
        start_sample_from_zero=True,
    )
    generator = QrCodeGenerator(study=study, saliva_distances=[10, 10, 10], contact_email="dum@my.com")
    generator.generate(output_dir=".")
```

#### Postprocessing Example

To be added

### Command Line Interface

For the preparation steps, CarWatch also provides a CLI for more convenient usage.
To use it, open a terminal session in the `carwatch` directory, and activate the corresponding python environment by
typing:

```
poetry shell
```

Then, the run the CLI by typing:

```
python generate_labels.py
```

You will then be prompted you to enter all the required information. The desired output files will automatically be
generated for you.
For more information about the prompted commands please run:

```
python generate_labels.py --help
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

We welcome contributions to CARWatch! To contribute, please fork this repository
and submit a pull request with your changes.

## Contact

If you have any questions or feedback about CARWatch, please contact
[Robert Richer](mailto:robert.richer@fau.de).
