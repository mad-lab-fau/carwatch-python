import sys
from pathlib import Path
from typing import Sequence, Union
import qrcode

from carwatch.utils.study import Study
from carwatch.utils.utils import assert_is_dir, sanitize_str_for_qr


class QrCodeGenerator:
    """Class that is used to generate a `.png` of a QR-Code including all relevant study properties required for usage
    in combination with the `_CAR Watch_` app. The QR-Code is unique for each study. It can be distributed to study
    participants to allow them configuring `_CAR Watch_` app on their personal devices.
    """

    def __init__(self, study: Study, saliva_distances: Union[int, Sequence[int]], contact_email: str,
                 check_duplicates: bool = False):
        """Generate QR-Code encoding all relevant study information encoded

        Parameters
        ----------
        study: :obj:`~carwatch.utils.Study`
           Study object for which QR-Code will be created
        saliva_distances: int or list
            Time distances between morning samples in minutes ordered chronologically.
            For s morning saliva samples, s-1 saliva distances need to be specified.
            If the distances are constant between all morning samples,
        contact_email: str
            E-mail address that App log data will be shared with
        check_duplicates: bool
            If set to ``True``, the CAR Watch app will check and alert if a barcode has been checked twice

        """
        self.study = study
        self.saliva_distances = self._sanitize_distances(saliva_distances)
        self.contact = contact_email
        self.check_duplicates = check_duplicates
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

        ``CARWATCH;N:<study_name>;D:<num_days>;S:<subject_list>;T:<saliva_distances>;E:<has_evening_sample>;M:<contact_email>;F:<check_duplicates>``

        """

        # sanitize inputs to prevent decoding issues
        forbidden = [";", ":", ","]
        study_name = sanitize_str_for_qr(self.study.study_name, forbidden)
        subject_names = []
        for name in self.study.subject_names:
            sanitized_name = sanitize_str_for_qr(name, forbidden)
            subject_names.append(sanitized_name)

        app_id = "CARWATCH"
        name_string = ",".join(str(dist) for dist in subject_names)
        distance_string = ",".join(str(dist) for dist in self.saliva_distances)

        # create encoding
        data = f"{app_id};" \
               f"N:{study_name};" \
               f"D:{self.study.num_days};" \
               f"S:{name_string};" \
               f"T:{distance_string};" \
               f"E:{int(self.study.has_evening_sample)};" \
               f"M:{self.contact};" \
               f"F:{int(self.check_duplicates)}"

        # create qr code
        img = qrcode.make(data)
        return img

    def _save_qr_img(self, qr_img):
        img_location = self.output_dir.joinpath(f"{self.output_name}.png")
        qr_img.save(img_location)

    def _sanitize_distances(self, saliva_distances: Union[int, Sequence[int]]) -> Sequence[int]:
        # required number of saliva distances
        num_morning_samples = self.study.num_samples
        if self.study.has_evening_sample:
            # evening sample counts into total number of distances
            num_morning_samples = num_morning_samples - 1
        if isinstance(saliva_distances, int):
            return [saliva_distances] * (num_morning_samples - 1)
        if isinstance(saliva_distances, list):
            # all elements are ints
            if all(isinstance(dist, int) for dist in saliva_distances):
                # length is correct
                if len(saliva_distances) == num_morning_samples - 1:
                    return saliva_distances
                raise ValueError(
                    f"Incorrect number of saliva distances provided! "
                    f"Needs to be {num_morning_samples - 1}, as "
                    f"{num_morning_samples} morning samples will be taken.")
            raise ValueError("Invalid data detected in saliva distances! All values need to be integers!")
        raise ValueError("Saliva distances data type is invalid! Needs to be int or list of ints.")
