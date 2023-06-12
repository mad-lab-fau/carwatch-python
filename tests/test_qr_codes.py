import pytest

from carwatch.qr_codes import QrCodeGenerator
from carwatch.utils import Study


def get_test_study() -> Study:
    study = Study(
        study_name="test_study",
        num_days=5,
        num_samples=10,
        num_subjects=20,
        subject_path=None,
        subject_prefix="VP_",
        subject_column="subject",
        has_evening_sample=True,
        start_sample_from_zero=True,
    )
    return study


def get_test_study_alternative() -> Study:
    study = Study(
        study_name="CAR_Test",
        num_days=15,
        num_samples=5,
        num_subjects=100,
        subject_path=None,
        subject_prefix="Person ",
        subject_column="subject",
        has_evening_sample=False,
        start_sample_from_zero=False,
    )
    return study


class TestQrCodeGenerator:
    @pytest.mark.parametrize(
        ("study", "saliva_distances", "contact_email", "check_duplicates", "enable_manual_scan", "expected"),
        [
            (
                get_test_study(),
                [30, 30, 30, 30, 30, 30, 30, 30, 30],
                "test@test.de",
                True,
                True,
                "CARWATCH;N:test_study;D:5;S:20;T:30,30,30,30,30,30,30,30,30,30;E:True;M:",
            )
        ],
    )
    def test_generate_qr_code(
        self, study, saliva_distances, contact_email, check_duplicates, enable_manual_scan, expected
    ):
        QrCodeGenerator(
            study=study,
            saliva_distances=saliva_distances,
            contact_email=contact_email,
            check_duplicates=check_duplicates,
            enable_manual_scan=enable_manual_scan,
        )
        # TODO: change function to return string instead of image (image will be generated in own function)
        #  assert qr_code._generate_qr_code()
        pass
