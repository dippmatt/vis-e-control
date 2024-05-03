# vis-e-control

Plotly Express Application to visualize Photovoltaic electricity produciton in Austria. Data is based on E-Control [Anlagenregister](https://anlagenregister.at), which lists all solar installations in Austria by district.

To translate the postcode of each district to the unique "Gemeinde code" the official [Gemeindeliste](https://www.statistik.at/verzeichnis/reglisten/gemliste_knz.xls) from Statistik Austria is used.

## Software Requirements

- Python. Tested using Python3.10 on Ubuntu 22.04

- Recommended packages: 

    - `python3.<X>-venv` (available e.g. as apt package).
Replace \<X\> with your version of python. Find your python version using `python3 --version`

    - Make, available in `build-essential` apt packages

## Getting started

- Install the required python requirements using `make init_env`.

## Run the app

- Run the necessary preprocessing: `make process_data`. This takes some time and fixes the raw database from E-Control.
- Launch the app `make run_app`
- Open a browser window of the [Dash Application](http://127.0.0.1:8050/)


## Documentation

- `make process_data` first preprocesses the raw dataset from Anlagenregister. This step reads the downloaded Excel files from Anlagenregister then performs elaborated preprocessing to
    
    1) Combine all Bundesländer into one database for Austria.
    2) Find the `Gemeindecode` for each entry in the database. The Anlagenregister stores entries by **Gemeindename** and **Postleizahl (PLZ)**. The PLZ is not a unique identifyer for a Gemeinde in Austria but the Gemeindecode is one. Unfortunately, a translation from PLZ to Gemeindecode is not easy due to several reasons:
        - The Anlagenregister from E-Control is a **Schemaless Database**, meaning that the database does not enforce certain rules for columns. This is due to manual errors when creating new entries and the lack of Schema Validation. Examples include different interpretations of the column `PLZ` such as `1040`, `A-1040`, `A/1040`, `1040 Wieden`, etc.
        - A one-to-many relationship from `Gemeindecode` to `PLZ`. Many Gemeinden have several PLZ (one primary and several auxiliary ones). - Some Gemeinden have the same PLZ.
    
        All these issues are addressed using pattern matching techniques and string comparison based on the **Levenshtein distance** to identify the most likly candidate for two Gemeinden to match if several options exist.
- The actual web app is then launched based on the preprocessed data using `make run_app`.



