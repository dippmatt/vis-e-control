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

- Then activate the environment using `source venv/bin/activate`



