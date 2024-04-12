import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np
import json
import subprocess

# Load your GeoJSON data (replace 'austria_districts.geojson' with your filename)
this_file = Path(__file__).parent.resolve()
austria_simplifyed = this_file / Path("..", "third_party", "GeoJSON-TopoJSON-Austria", "2021", "simplified-99.5", "gemeinden_995_geo.json")

class Anlagenregister():
    """
    Class to load & display the data from the Anlagenregister
    """
    def __init__(self, dataset: Path):
        self.database_path = dataset / Path("anlagenregister.feather")

        if not self.database_path.exists():
            styria = pd.read_excel(dataset / Path("styria.xlsx"))
            tyrol = pd.read_excel(dataset / Path("tyrol.xlsx"))
            vienna = pd.read_excel(dataset / Path("vienna.xlsx"))
            vorarlberg = pd.read_excel(dataset / Path("vorarlberg.xlsx"))
            upper_austria = pd.read_excel(dataset / Path("upper_austria.xlsx"))
            salzburg = pd.read_excel(dataset / Path("salzburg.xlsx"))
            lower_austria = pd.read_excel(dataset / Path("lower_austria.xlsx"))
            burgenland = pd.read_excel(dataset / Path("burgenland.xlsx"))
            carinthia = pd.read_excel(dataset / Path("carinthia.xlsx"))

            combined_df = pd.concat([styria, tyrol, vienna, vorarlberg, upper_austria, salzburg, lower_austria, burgenland, carinthia], ignore_index=True)
            # delete 'ID' column
            combined_df.drop(columns=['ID'], inplace=True)
            combined_df.to_feather(self.database_path)
            self.database = pd.read_feather(self.database_path)
        else:
            self.database = pd.read_feather(self.database_path)
            # print the set of all 'Bundesland' values
            
        import sys; sys.exit(0)

        # Store Feather 
        print("Storing feather")
        print(f"Styria has {len(self.styria)} rows.")
        print(f"Tyrol has {len(self.tyrol)} rows.")
        combined_df.to_feather('tmp.feather')
        combined_df = pd.read_feather('tmp.feather')
        print(f"Feather has {len(combined_df)} rows.")
        print(combined_df.head())

        st = combined_df[combined_df['Bundesland'] == 'ST']
        ty = combined_df[combined_df['Bundesland'] == 'T']
        print(f"Styria has {len(st)} rows.")
        print(f"Tyrol has {len(ty)} rows.")
        print(st.head())
        print(ty.head())
        print()

 
        import sys; sys.exit(0)

        
        
        
        self.plz2gkz = pd.read_excel(dataset / Path("gemliste_knz.xls"))


def main():
    this_file = Path(__file__).parent.resolve()
    dataset = this_file / Path("..", "dataset", "e-control-data")
    data_save_path = this_file / Path("..", "dataset", "anlagenregister.parquet")
    anlagenregister = Anlagenregister(dataset)

if __name__ == "__main__":
    main()