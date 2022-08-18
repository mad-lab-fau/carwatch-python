from carwatch.labels import LabelGenerator, Study

if __name__ == "__main__":
    study = Study(study_name="TestStudy", num_days=3, num_subjects=4, num_saliva_samples=5, has_evening_salivette=True)
    generator = LabelGenerator(study=study, add_name=True, has_barcode=False)
    generator.generate(output_dir="./output_labels", debug=True)
