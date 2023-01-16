from carwatch.labels import CustomLayout, LabelGenerator
from carwatch.qr_codes import QrCodeGenerator
from carwatch.utils import Study

if __name__ == "__main__":
    study = Study(
        study_name="ExampleStudy",
        num_days=3,
        num_subjects=15,
        num_samples=5,
        has_evening_sample=True,
    )
    generator = QrCodeGenerator(study=study, saliva_distances=[10, 10, 10, 10], contact_email="dum@my.com")
    generator.generate(output_dir=".")
