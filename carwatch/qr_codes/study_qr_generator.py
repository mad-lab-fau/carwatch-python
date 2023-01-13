import sys
from pathlib import Path
from typing import Sequence, Union
import qrcode

from carwatch.utils.study import Study
from carwatch.utils.utils import assert_is_dir


class QrCodeGenerator:
    """Class that is used to generate a `.png` of a QR-Code including all relevant study properties required for usage
    in combination with the `_CAR Watch_` app. The QR-Code is unique for each study. It can be distributed to study
    participants to allow them configuring `_CAR Watch_` app on their personal devices.
    """

    def __init__(self, study: Study, saliva_distances: Sequence[int], contact_email: str):
        """Generate QR-Code encoding all relevant study information encoded

        Parameters
        ----------
        study: :obj:`~carwatch.utils.Study`
           Study object for which QR-Code will be created
        saliva_distances: list
            Time distances between morning saliva samples in chronological order.
            For s saliva samples, s-1 saliva distances need to be specified.
        contact_email: str
            E-mail address that App log data will be shared with

        """
        self.study = study
        self.saliva_distances = saliva_distances
        self.contact = contact_email
        self.output_dir = None
        self.output_name = f"qr_code_{self.study.study_name}"

    def generate(self,
                 output_dir: str = ".",
                 output_name: Union[str, None] = None
                 ):
        """Generate a `*.png` file with QR code according to the properties of the created ``QrCodeGenerator``.

        Parameters
        ----------
        output_dir: str
            Path to the directory where the generated QR-Code will be stored
        output_name: str, optional
            Filename of the generated QR-Code

        """
        output_dir = Path(output_dir)
        try:
            assert_is_dir(output_dir)
        except ValueError as e:
            print(e)
            sys.exit(1)
        self.output_dir = output_dir
        if output_name:
            if output_name.endswith(".png"):
                # store without file ending
                output_name = output_name.rsplit(".", 1)[0]
            self.output_name = output_name
        qr_img = self._generate_qr_code()
        self._save_qr_img(qr_img)

    def _generate_qr_code(self):
        """Translate study data into  a QR-Code in the following format:

        ``CARWATCH;N:<study_name>;D:<num_days>;S:<subject_list>;T:<saliva_distances>;E:<has_evening_salivette>;M:<contact_email>``

        """

        app_id = "CARWATCH"
        data = f"{app_id};" \
               f"N:{self.study.study_name};" \
               f"D:{self.study.num_days};" \
               f"S:{self.study.subject_names};" \
               f"T:{self.saliva_distances};" \
               f"E:{self.study.has_evening_salivette};" \
               f"M:{self.contact}"
        img = qrcode.make(data)
        return img

    def _save_qr_img(self, qr_img):
        img_location = self.output_dir.joinpath(f"{self.output_name}.png")
        qr_img.save(img_location)
