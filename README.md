# DroneNLP Dataset

This repository contains the source data, cleansed files, and annotation logs for the **DroneNLP** project. The dataset is a collection of drone flight log messages designed to support research in Natural Language Processing for drone diagnostics, safety, and forensics.

---

## Repository Structure

The dataset is organized into a clear, hierarchical structure to reflect our data processing pipeline, ensuring transparency and reproducibility.

```
dataset/
├── raw/                            # Contains all original, un-cleansed data sources
│   ├── air_data/
│   │   └── raw-air-data.xlsx       # Original collection of 499 messages from AirData UAV
│   └── vto_labs/                   
│       └── parsed.xlsx             # Original collection of VTO Lab's messages
│
├── processed/                      # Contains data files after cleansing procedures
│   ├── air_data/
│   │   ├── corrected_data_step_1.xlsx  # After Step 1: Period correction
│   │   ├── corrected_data_step_2.xlsx  # After Step 2: Punctuation & space correction
│   │   ├── corrected_data_step_3.xlsx  # After Step 3: Over-generalized message correction
│   │   ├── correction_log_step_2.xlsx
│   │   └── correction_log_step_3.xlsx
│   └── vto_labs/
|       └── parsed-cleansed.csv     # A collection of VTO Lab's messages from all flight logs
│
├── annotated/                      # The final, task-specific annotated datasets
│   ├── problem_identification/         # Dataset for the Problem Identification task
│   │   ├── train/
│   │   └── test/
│   │
│   └── event_recognition/              # Dataset for the Event Recognition task
│       ├── train/
│       └── test/
│
└── .gitignore                      # Ensures non-essential files are not committed
```
---

## Download and Usage

The full, versioned dataset is hosted on **Zenodo** (forthcoming), providing a persistent and citable DOI. We highly recommend using the Zenodo link for stable research.

<!-- * **Zenodo Page:** [https://doi.org/YOUR_ZENODO_DOI_HERE]
* **CLI Download:** For easy programmatic download, use `zenodo_get`. -->

For the latest, in-progress updates and individual files, you can browse this GitHub repository.

## Citation

If you use this dataset in your research, please cite our corresponding publication and the dataset's Zenodo DOI. You can find detailed citation instructions on our [project website](https://dronenlp.github.io/documentation/publications/).

---

## License

This dataset is released under the **MIT License**. The full text of the license is available in the `LICENSE` file within this repository.