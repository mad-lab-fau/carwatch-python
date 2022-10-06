from carwatch.labels import CustomLayout, LabelGenerator, Study

if __name__ == "__main__":
    study = Study(
        study_name="ExampleStudy",
        num_days=3,
        subject_path="subjects.csv",
        num_saliva_samples=5,
        has_evening_salivette=True,
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
    generator.generate(output_dir="./output_labels", debug=True, layout=layout)
