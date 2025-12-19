## Evidence Dataset

This folder contains the flight log evidence used for evaluation and demonstration of the forensic tool.
To ensure forensic soundness and reproducibility, we publish the logs in three formats:

#### Folder Structure
```
src/evidence/
│
├── raw/          # Original encrypted flight logs (as acquired from DJI Fly app)
│     ├── DJIFlightRecord_2025-06-27_[03-34-35].txt
│     ├── ...
│     ├── hash_check.py # script to check the file hash
│     └── hash.json     # the hash of each file
│
├── decrypted/    # Decrypted logs (derived from raw)
│     ├── DJIFlightRecord_2025-06-27_[03-34-35].csv
│     ├── ...
│     └── parse.py     # script to extract timestamp and log messages
│
├── parsed/       # Logs parsed into simplified format (timestamp + message only)
│     ├── flight_log_1.xlsx
│     └── ...
│
└── README.md     # This documentation
```

### Acquisition

- Source: Logs were extracted from the Android DJI Fly app after operating a DJI FPV drone.

- Format: Original files are encrypted `.txt` files with filenames in the form: `DJIFlightRecord_YYYY-MM-DD_[HH-MM-SS].txt`

### Decryption

- Method: The raw files were decrypted using [DJI Phantom Help Log Viewer](https://www.phantomhelp.com/logviewer/upload/).

- Output: Human-readable `.csv` logs containing full event details.

- Naming convention: The decrypted file retains the original base name with `.csv` extension.

### Parsing

- Method: A custom parser (provided in `src/evidence/decrypted/parse.py`) was used to extract only the timestamp and message fields.
- Output: Simplified `.xlsx` files used as input to the CLI forensic pipeline.
- Naming convention: Sequentially numbered as `flight_log_N.xlsx`.

### Integrity Verification

The raw files are the primary evidence and must not be altered. The MD5, SHA1, and SHA-256 hashes are stored in `src/evidence/raw/hash.json`. Run `python src/evidence/raw/hash_check.py` to verify the hash of the raw files. Below are the SHA-256 of all raw files.

| Raw File                                     | SHA-256 Hash |
| -------------------------------------------- | ------------ |
| DJIFlightRecord\_2024-11-10\_\[03-09-29].txt | `24850c8c1656cfdb6e21af86fea9195b350b7a82080a612ae4e8fce8fc4ead7f`   |
| DJIFlightRecord\_2025-05-12\_\[08-01-12].txt | `160a94f3bba0c34f562e0af3c192b5246ad2fe1eb0533850d0a4f5b831d260bd`   |
| DJIFlightRecord\_2025-05-12\_\[08-20-56].txt | `6ed92cfea8a7619fc3a874532a77e893f2a7e095c33071d291da2a9d0d35bfb0`          |
| DJIFlightRecord\_2025-06-27\_\[03-23-15].txt | `1854ae08d621c02721f27fc5b4966c9e51000d1bd5b1e04bf1d692ca076e53e1`          |
| DJIFlightRecord\_2025-06-27\_\[03-27-42].txt | `b2d45d61fba507c6665a5f231a375dd2a1ea4489de5559266a1853edb62e03eb`          |
| DJIFlightRecord\_2025-06-27\_\[03-31-40].txt | `56cfef1fc8715d2d9268b13eeae9f39f5403977f82d0e865fc794ab41d29a7f8`          |
| DJIFlightRecord\_2025-06-27\_\[03-34-35].txt | `a3b0ffb9d801a0d1f5bc8106d04f92251b995a576961d8106de6bf748adaf12e`          |

### Mapping Between Formats
For convinience, the parsed file used integer index as part of the name. Below are the mapping from the raw filenames to the parsed filenames.

| Raw File                                     | Flight Log |
| -------------------------------------------- | ------------ |
| DJIFlightRecord\_2024-11-10\_\[03-09-29].txt | `flight_log_1.xlsx`   |
| DJIFlightRecord\_2025-05-12\_\[08-01-12].txt | `flight_log_2.xlsx`   |
| DJIFlightRecord\_2025-05-12\_\[08-20-56].txt | `flight_log_3.xlsx`          |
| DJIFlightRecord\_2025-06-27\_\[03-23-15].txt | `flight_log_4.xlsx`          |
| DJIFlightRecord\_2025-06-27\_\[03-27-42].txt | `flight_log_5.xlsx`          |
| DJIFlightRecord\_2025-06-27\_\[03-31-40].txt | `flight_log_6.xlsx`          |
| DJIFlightRecord\_2025-06-27\_\[03-34-35].txt | `flight_log_7.xlsx`          |


### Ground Truth (Qualitative Analysis)

Each log may contain multiple incident scenarios (e.g., communication issues, hardware failures, environmental interference). A manual investigation is conducted to extract key events from each flight log and identify the corresponding problem types.

| Flight Log          | Problem Type | Key Events |
| ------------------- | ------------ | ------------ |
| `flight_log_1.xlsx` | Parameter Violation, Communication Issue   | Gimbal pitch axis endpoint reached.; Image transmission signal weak.; RC signal lost.; |
| `flight_log_2.xlsx` | Parameter Violation, Communication Issue   | Image transmission signal weak.; RC signal lost.; No image transmission.; RC signal weak.; Gimbal pitch axis endpoint reached.; |
| `flight_log_3.xlsx` | Communication Issue          | Image transmission signal weak.; RC signal lost.; No image transmission.; RC signal weak.; Downlink Lost.; |
| `flight_log_4.xlsx` | Software Issue, Hardware Issue, Communication Issue          | Gimbal auto check failed.; Gimbal stuck.; Image transmission signal weak.; RC signal lost.; Downlink Lost.; RC signal weak.; |
| `flight_log_5.xlsx` | Hardware Issue, Communication Issue, Surrounding Environment Issue, Parameter Violation          | Compass error.; Ambient light too low.; RC signal lost.; Gimbal pitch axis endpoint reached.; Downward ambient light too low.; RC signal weak.; |
| `flight_log_6.xlsx` | Hardware Issue, Surrounding Environment Issue          | Compass error.; Downward ambient light too low.; Forward ambient light too low.; Low battery.; Remaining battery only enough for RTH.; Low battery RTH.; | 
| `flight_log_7.xlsx` | Communication Issue, Surrounding Environment Issue          |  Forward ambient light too low.; Downward ambient light too low.; Ambient light too low.; RC signal lost.; Image transmission signal weak.; Image transmission signal lost.; Downlink Lost.; RC signal weak.; |
