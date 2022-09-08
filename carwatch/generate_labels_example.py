from carwatch.labels import LabelGenerator, Study, CustomLayout

if __name__ == "__main__":
    study = Study(study_name="ExampleStudy", num_days=3, num_subjects=4, num_saliva_samples=5, has_evening_salivette=True)
    generator = LabelGenerator(study=study, add_name=True, has_barcode=True)
    layout = CustomLayout(num_cols=4, num_rows=10, left_margin=10, right_margin=10, top_margin=20, bottom_margin=20,
                          inter_col=2, inter_row=2)
    generator.generate(output_dir="./output_labels", debug=True, layout=layout)
