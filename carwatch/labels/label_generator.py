from itertools import product
from pathlib import Path
from typing import Union

import barcode
import cairosvg
import numpy as np

from carwatch.labels.utils import _assert_is_dir, _tex_to_pdf, Study
from carwatch.labels.print_layout import AveryZweckformJ4791Layout, PrintLayout


class LabelGenerator:
    """Class that is used to generate printable *.pdf files with labels for all saliva samples taken within a study."""
    EAN8 = barcode.get_barcode_class('ean8')

    def __init__(self, study: Study, has_barcode: bool = False, add_name: bool = False):
        """Class that is used to generate printable *.pdf files with labels for all saliva samples taken within a study.
        If the parameter `add_name` is `True` then the text next to the barcode will have the following layout:
        ```
        <study_name>_<subject_id>
        T<day>_S<saliva_id or A for evening sample>
        ```
        For example:
        ```
        DiPsyLab_01
        T1_S4
        ```

        If `add_name` is set to `False` then only the second line is printed:
        ```
        T<day>_S<saliva_id or A for evening sample>
        ```
        For example:
        ```
        T0_SA
        ```
        Parameters
        ----------
        study: :class: `carwatch.labels.Study`
            Study object for which labels will be created
        has_barcode: bool, optional
            Whether a barcode of type `EAN-8` will be printed on each label
        add_name: bool, optional
            Whether the name of the study will be printed on each label
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

    def generate(self, output_dir: str = ".", output_name: Union[str, None] = None,
                 layout: PrintLayout = AveryZweckformJ4791Layout(), debug=False):
        """
        Generates a *.pdf file with labels according to the LabelGenerator's properties
        Parameters
        ----------
            output_dir: str
            output_name: Union[str, None]
            layout: :class: `PrintLayout`
        """
        output_dir = Path(output_dir)
        _assert_is_dir(output_dir)
        self.output_dir = output_dir
        if output_name:
            self.output_name = output_name
        self.layout = layout
        self._create_output_dir()
        self.barcode_ids, self.barcodes = self._generate_barcodes()
        self.barcode_paths = self._export_barcodes_to_pdf()
        self._generate_tex_file()
        _tex_to_pdf(self.output_dir, self.output_name + ".tex")
        self._clear_intermediate_results(delete_img_dir=True, debug=debug)

    def _generate_barcodes(self):
        """
        Generates barcode ids and corresponding EAN8-codes using the following scheme:
        `pppddss`, where p is the participant id, d is the study day, and s is the number of the saliva sample of that day

        Returns
        -------
        barcode_ids: np.array
            1-dim array containing all ids of the generated barcodes
        barcodes: np.array
            1-dim array containing :class: barcode.ean.EuropeanArticleNumber8 objects that represent the EAN8-barcodes
            corresponding to `barcode_ids`
        """
        barcode_ids = ["{:03d}{:02d}{:02d}".format(subj, day, saliv) for subj, day, saliv in
                       list(product(self.study.subject_ids, self.study.day_ids, self.study.saliva_ids))]
        # sort the ids
        barcode_ids = np.array(sorted(barcode_ids))
        # generate the codes
        barcodes = np.vectorize(lambda x: self.EAN8(x))(barcode_ids)  # [EAN8(barcode) for barcode in barcode_ids])
        return barcode_ids, barcodes

    def _export_barcodes_to_pdf(self):
        """Creates *.svg files with barcodes from :class: barcode.ean.EuropeanArticleNumber8 objects
        and converts them to *.pdf files"""
        img_path = self.output_dir.joinpath("img")
        options = {"quiet_zone": 1, "font_size": 8, "text_distance": 3}  # configure label font
        barcode_paths = np.array(
            [barcode_object.save(img_path.joinpath('barcode_{}'.format(barcode_id)), options=options) for
             barcode_id, barcode_object in
             zip(self.barcode_ids, self.barcodes)])
        for path in barcode_paths:
            cairosvg.svg2pdf(
                file_obj=open(path, "rb"), write_to=path.replace('svg', 'pdf'))
        return barcode_paths

    def _create_output_dir(self):
        """if not existing, creates `{output_dir}/img` directory for intermediate files and clears it"""
        img_path = self.output_dir.joinpath("img")
        img_path.mkdir(exist_ok=True)
        self._clear_intermediate_results()

    def _clear_intermediate_results(self, delete_img_dir=False, debug=False):
        """removes intermediate *.svg and *.pdf files with individual labels from `{output_dir}/img`
        and the `img`-folder itself if `delete_img_dir` is True"""
        img_path = self.output_dir.joinpath("img")
        for f in img_path.glob("*"):
            if f.suffix in ('.svg', '.pdf'):
                f.unlink()
        if delete_img_dir:
            img_path.rmdir()
        if not debug:
            for f in self.output_dir.glob("*"):
                if f.suffix in ('.log', '.aux', '.tex'):
                    f.unlink()

    def _generate_tex_file(self):
        import importlib.resources as pkg_resources
        from carwatch import labels  # package containing tex template
        # copy tex template to output dir
        template = pkg_resources.read_text(labels, "barcode_template.tex")
        with open(self.output_dir.joinpath(self.output_name + ".tex"), "w+") as fp:
            fp.write(template)
        # write generated body to output dir
        body_str = self._generate_tex_body()
        with open(self.output_dir.joinpath("body.tex"), "w+") as fp:
            fp.write(body_str)

    def _generate_label_tex(self, barcode_id: int):
        day = int(barcode_id // 100) % 100
        sample = barcode_id % 100
        subject = int(barcode_id // 1e4)
        label_head = r"\genericlabel" + "\n" + r"\begin{tabular}"
        label_foot = r"\end{tabular}" + "\n\n"
        table_content = ""
        if self.has_barcode:
            # create table with 2 columns
            table_properties = r"{m{0.45\linewidth} m{0.4\linewidth}}" + "\n"
            # add barcode to first column
            table_content += rf"\includegraphics[height={self.layout.row_height}mm]{{img/barcode_{subject:03d}{day:02d}{sample:02d}.pdf}} &"
            font_size = r"\tiny"  # decrease font size to make it fit next to barcode
        else:
            # create table with only one column
            table_properties = r"{c}"
            font_size = ""  # use default font size
            # center text in label
            label_head = r"\genericlabel" + "\n" + r"\begin{center}" + "\n" + r"\begin{tabular}"
            label_foot = r"\end{tabular}" + "\n" + r"\end{center}" + "\n\n"
        if self.add_name:
            if all([sample == self.study.num_saliva_samples, self.study.has_evening_salivette]):
                # if last sample of the day is evening salivette, it is marked as "TA"
                sample = "A"
            # add study name, subject id, day, and sample to second column
            if self.has_barcode:
                # insert infos as one row in the second column
                table_content += rf"\centering{font_size}{{{self.study.study_name}\_{subject:02d}\newline T{day}\_S{sample}}}" + "\n"
            else:
                # insert infos centered in two rows
                table_content += rf"{font_size}{{{self.study.study_name}\_{subject:02d}}}\\{{T{day}\_S{sample}}}" + "\n"
        else:
            # add day and sample to second column
            table_content += rf"\centering{font_size}{{T{day}\_S{sample}}}" + "\n"
        label_tex = label_head + table_properties + table_content + label_foot
        return label_tex

    def _generate_tex_body(self):
        tex_head = r"\begin{labels}" + "\n"
        tex_foot = r"\end{labels}"
        tex_body = ""
        for sample in self.barcode_ids:
            # add tex code for every label to body
            tex_body += self._generate_label_tex(int(sample))
        return tex_head + tex_body + tex_foot
