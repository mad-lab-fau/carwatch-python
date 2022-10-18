import importlib.resources as pkg_resources
import sys
from itertools import product
from pathlib import Path
from typing import Union

import barcode
import cairosvg
import numpy as np

from carwatch.labels.print_layout import AveryZweckformJ4791Layout, PrintLayout
from carwatch.labels.utils import Study, _assert_is_dir, _tex_to_pdf, _write_to_file


class LabelGenerator:
    """Class that is used to generate printable `*.pdf` files with labels for all saliva samples taken within a study.

    Tested for labels of type `_Avery Zweckform J4791_` (48 labels per A4-sheet) and only intended to be used for print
    labels in A4 format. Note that for smaller labels, text overflows might occur.
    """

    EAN8 = barcode.get_barcode_class("ean8")
    MAX_NAME_LEN = 12

    def __init__(self, study: Study, has_barcode: bool = False, add_name: bool = False):
        """Generate printable PDF files with labels for all saliva samples taken within a study.

        If the parameter ``add_name`` is ``True`` then the text next to the barcode will have the following layout:
        ```
        <study_name>_<subject_id>
        T<day>_S<saliva_id or A for evening sample>
        ```
        For example:
        ```
        ExampleStudy_01
        T1_S4
        ```

        If ``add_name`` is set to ``False`` then only the second line is printed:
        ```
        T<day>_S<saliva_id or A for evening sample>
        ```
        For example:
        ```
        T0_SA
        ```

        Parameters
        ----------
        study: :obj:`~carwatch.labels.Study`
            Study object for which labels will be created
        has_barcode: bool, optional
            Whether a barcode of type `EAN-8` will be printed on each label
        add_name: bool, optional
            Whether the name of the study will be printed on each label

        Examples
        --------
        Create a Study and print labels for a custom layout
        >>> from carwatch.labels import LabelGenerator, Study, CustomLayout
        >>> Study(
        >>>     study_name="ExampleStudy", num_days=3, num_subjects=4, num_saliva_samples=5, has_evening_salivette=True
        >>> )
        >>> generator = LabelGenerator(study=study, add_name=True, has_barcode=True)
        >>> layout = CustomLayout(
        >>>     num_cols=4, num_rows=10, left_margin=10, right_margin=10,
        >>>     top_margin=20, bottom_margin=20, inter_col=2, inter_row=2
        >>> )
        >>> generator.generate(output_dir="./output_labels", layout=layout)

        """
        self.study = study
        self.has_barcode = has_barcode
        self.add_name = add_name
        self.output_dir = None
        self.output_name = f"barcodes_{self.study.study_name}"
        self.layout = None
        self.barcode_paths = None
        self.barcodes = None
        self.barcode_ids = None

    def generate(
        self,
        output_dir: str = ".",
        output_name: Union[str, None] = None,
        layout: PrintLayout = AveryZweckformJ4791Layout(),
        debug=False,
    ):
        """Generate a `*.pdf` file with labels according to the properties of the created ``LabelGenerator``.

        Parameters
        ----------
        output_dir: str
            Path to the directory where the generated label-PDF will be stored
        output_name: str, optional
            Filename of the generated label-PDF
        layout: :obj:`~carwatch.labels.PrintLayout`, optional
            Type of label paper used for printing of the labels
        debug: bool, optional
            If set to true, auxiliary files generated by latex, e.g., `*.log`-file,
            will be preserved for debugging purpose;
            furthermore, the borders of each individual label will be drawn in the generated PDF

        """
        output_dir = Path(output_dir)
        try:
            _assert_is_dir(output_dir)
        except ValueError as e:
            print(e)
            sys.exit(1)
        self.output_dir = output_dir
        if output_name:
            if output_name.endswith(".pdf"):
                # store without file ending
                output_name = output_name.rsplit(".", 1)[0]
            self.output_name = output_name
        self.layout = layout
        self._create_output_dir()
        self.barcode_ids, self.barcodes = self._generate_barcodes()
        self.barcode_paths = self._export_barcodes_to_pdf()
        self._generate_tex_file(debug=debug)
        try:
            _tex_to_pdf(self.output_dir, self.output_name + ".tex")
        except RuntimeError as e:
            print(e)
        self._clear_intermediate_results(delete_img_dir=True, debug=debug)

    def _generate_barcodes(self):
        """Generate barcode ids and corresponding EAN8-codes.

        Barcode IDs and corresponding EAN8-codes are generated using the following scheme:

            `pppddss`

        where p is the participant id, d is the study day, and s is the number of the saliva sample of that day.

        Returns
        -------
        barcode_ids: :class:`~np.array`
            1-dim array containing all 8-digit ids of the generated barcode objects
        barcodes: :class:`~np.array`
            1-dim array containing :class:`~barcode.ean.EuropeanArticleNumber8` objects that represent the EAN8-barcodes
            corresponding to ``barcode_ids``

        """
        barcode_ids = [
            f"{subj:03d}{day:02d}{saliv:02d}"
            for subj, day, saliv in list(
                product(self.study.subject_indices, self.study.day_indices, self.study.saliva_indices)
            )
        ]
        # sort the ids
        barcode_ids = np.array(sorted(barcode_ids))
        # generate the codes
        barcodes = np.vectorize(self.EAN8)(barcode_ids)  # [EAN8(barcode) for barcode in barcode_ids])
        return barcode_ids, barcodes

    def _export_barcodes_to_pdf(self):
        """Create `*.svg` files from barcodes and convert them to `.pdf` files.

        The barcodes are first created as svg files from :class:`~barcode.ean.EuropeanArticleNumber8` objects
        and then converted to `*.pdf` files.

        Returns
        -------
        barcode_paths: :class:`~np.array`
            List of paths to pdf files displaying the generated barcodes

        """
        img_path = self.output_dir.joinpath("img")
        options = {"quiet_zone": 1, "font_size": 8, "text_distance": 3}  # configure label font
        barcode_paths = np.array(
            [
                barcode_object.save(img_path.joinpath(f"barcode_{barcode_id}"), options=options)
                for barcode_id, barcode_object in zip(self.barcode_ids, self.barcodes)
            ]
        )
        for path in barcode_paths:
            with open(path, "rb") as file:
                cairosvg.svg2pdf(file_obj=file, write_to=path.replace("svg", "pdf"))
        return barcode_paths

    def _create_output_dir(self):
        """Create output directory for intermediate files or clears it (if already exists).

        The directory name will be ``{output_dir}/img``.

        """
        img_path = self.output_dir.joinpath("img")
        img_path.mkdir(exist_ok=True)
        self._clear_intermediate_results()

    def _clear_intermediate_results(self, delete_img_dir=False, debug=False):
        """Remove intermediate `*.svg` and `*.pdf` files with individual labels.

        All intermediate files are removed from ``{output_dir}/img``.
        If ``delete_img_dir`` is set to ``True``, the ``img`` folder itself will additionally be removed.

        """
        img_path = self.output_dir.joinpath("img")
        for f in img_path.glob("*"):
            if f.suffix in (".svg", ".pdf"):
                f.unlink()
        if delete_img_dir:
            img_path.rmdir()
        if not debug:
            for f in self.output_dir.glob("*"):
                if f.suffix in (".log", ".aux", ".tex"):
                    f.unlink()

    def _generate_tex_file(self, debug: bool = False):
        """Generate LaTeX code for all individual labels.

        The generated LaTeX code is then inserted into a tex-template and the result is written to
        ``{output_dir}/{output_name}.tex``.

        """
        from carwatch import labels  # package containing tex template # pylint:disable=import-outside-toplevel

        # copy tex template to output dir
        # TODO: is this way really necessary? why don't you just read in the file in a regular way?
        template = pkg_resources.read_text(labels, "barcode_template.tex")
        _write_to_file(self.output_dir.joinpath(self.output_name + ".tex"), template)

        # write generated properties to output dir
        property_str = self._generate_tex_label_properties(debug)
        _write_to_file(self.output_dir.joinpath("properties.tex"), property_str)

        # write generated body to output dir
        body_str = self._generate_tex_body()
        _write_to_file(self.output_dir.joinpath("body.tex"), body_str)

    def _generate_label_tex(self, barcode_id: int):
        """Generate LaTeX code for a certain label.

        The label is generated based on the specified properties of :obj:`~carwatch.labels.LabelGenerator`.

        Parameters
        ----------
        barcode_id: int
            8-digit number of the respective barcode with the format `cpppddss`
            with c: check digit, p: participant id, d: study day, s: saliva sample

        """
        day = int(barcode_id // 100) % 100
        sample = barcode_id % 100
        subject = int(barcode_id // 1e4)
        subject_name = f"{subject:02d}"
        if self.study.subject_ids:
            # subject has a certain identifier and not just a number
            subject_name = self.study.subject_ids[subject - 1]
        # label is realized with latex table
        label_head = r"\genericlabel" + "\n" + r"\begin{tabular}"
        label_foot = r"\end{tabular}" + "\n\n"
        table_content = ""
        if self.has_barcode:
            # create table with 2 columns
            table_properties = r"{m{0.45\linewidth} m{0.4\linewidth}}" + "\n"
            # add barcode to first column
            table_content += rf"\includegraphics[height={self.layout.get_label_height() - 4}\
            mm,width=\linewidth,keepaspectratio]{{img/barcode_{subject:03d}{day:02d}{sample:02d}.pdf}} &"
            font_size = r"\tiny"  # decrease font size to make it fit next to barcode
        else:
            # create table with only one column
            table_properties = r"{c}"
            font_size = ""  # use default font size
            # center text in label
            label_head = r"\genericlabel" + "\n" + r"\begin{center}" + "\n" + r"\begin{tabular}"
            label_foot = r"\end{tabular}" + "\n" + r"\end{center}" + "\n\n"
        if self.add_name:
            delimiter = r"\_"
            if len(self.study.study_name) + len(subject_name) > LabelGenerator.MAX_NAME_LEN:
                # insert linebreak between study name and subject id to prevent overflow
                delimiter = r"\linebreak "
            if all([sample == self.study.num_saliva_samples, self.study.has_evening_salivette]):
                # if last sample of the day is evening salivette, it is marked as "TA"
                sample = "A"
            # add study name, subject id, day, and sample to second column
            if self.has_barcode:
                # insert infos as one row in the second column
                table_content += (
                    rf"\centering{font_size}{{{self.study.study_name}{delimiter}{subject_name}"
                    + rf"\newline T{day}\_S{sample}}}"
                    + "\n"
                )
            else:
                # insert infos centered in two rows
                table_content += (
                    rf"{font_size}{{{self.study.study_name}{delimiter}{subject_name}}}\\{{T{day}\_S{sample}}}\n"
                )
        else:
            # add day and sample to second column
            table_content += rf"\centering{font_size}{{T{day}\_S{sample}}}" + "\n"
        label_tex = label_head + table_properties + table_content + label_foot
        return label_tex

    def _generate_tex_label_properties(self, debug: bool) -> str:
        """Define arrangement of labels based on specified :obj:`~carwatch.labels.PrintLayout`."""
        tex_properties = ""
        tex_properties += rf"\LabelCols={self.layout.num_cols}" + "\n"  # number of columns of labels per page
        tex_properties += rf"\LabelRows={self.layout.num_rows}" + "\n"  # number of rows of labels per page
        tex_properties += rf"\LeftPageMargin={self.layout.left_margin}mm" + "\n"  # margin to the left
        tex_properties += rf"\RightPageMargin={self.layout.right_margin}mm" + "\n"  # margin to the right
        tex_properties += rf"\TopPageMargin={self.layout.top_margin}mm" + "\n"  # margin to the top
        tex_properties += rf"\BottomPageMargin={self.layout.bottom_margin}mm" + "\n"  # margin to the bottom
        tex_properties += rf"\InterLabelColumn={self.layout.inter_col}mm" + "\n"  # gap between columns of labels
        tex_properties += rf"\InterLabelRow={self.layout.inter_row}mm" + "\n"  # gap between rows of labels
        tex_properties += r"\LeftLabelBorder=1mm" + "\n"  # minimum gap between text and label border on the left
        tex_properties += r"\RightLabelBorder=1mm" + "\n"  # minimum gap between text and label border on the right
        tex_properties += r"\TopLabelBorder=2mm" + "\n"  # minimum gap between text and label border on the top
        tex_properties += r"\BottomLabelBorder=2mm" + "\n"  # minimum gap between text and label border on the bottom
        if debug:
            tex_properties += r"\LabelGridtrue" + "\n"  # draw label borders
        return tex_properties

    def _generate_tex_body(self):
        """Iterate over all barcodes and generate corresponding LaTeX code."""
        tex_head = r"\begin{labels}" + "\n"
        tex_foot = r"\end{labels}"
        tex_body = ""
        for sample in self.barcode_ids:
            # add tex code for every label to body
            tex_body += self._generate_label_tex(int(sample))
        return tex_head + tex_body + tex_foot
