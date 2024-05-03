import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as  np
import json
import subprocess
from tqdm import tqdm
from rapidfuzz import fuzz
from colorama import Fore
from dash import Dash, dcc, html, Input, Output


class Anlagenregister():
    """
    Class to load & display the data from the Anlagenregister
    """
    def __init__(self, dataset: Path):
        # Load your GeoJSON data (replace 'austria_districts.geojson' with your filename)
        this_file = Path(__file__).parent.resolve()
        self.austria_simplifyed = this_file / Path("..", "third_party", "GeoJSON-TopoJSON-Austria", "2021", "simplified-99.5", "gemeinden_995_geo.json")
        with open(self.austria_simplifyed) as f:
            self.gemeinden_austria_geojson = json.load(f)

        # append the Gemeindecode (GCD) to the geojson id field, to make them visible in the map
        # the GCD is the link to the data in the Anlagenregister
        for i, elem in enumerate(self.gemeinden_austria_geojson['features']):
            elem["id"] = elem['properties']['iso']
        
        ################################# Gemeindeliste ################################
        ###                                                                          ###
        ### The file 'gemliste_knz.xls' contains a mapping from PLZ to Gemeinde code ###
        ###                                                                          ###
        ################################################################################

        gemeindeliste_path = (dataset / Path("gemliste_knz.xls")).resolve()
        assert gemeindeliste_path.exists(), f"The file {gemeindeliste_path} does not exist."
        self.gemeindeliste_pd = pd.read_excel(gemeindeliste_path, skiprows=3)#, dtype={'Gemeinde code': int, 'PLZ des Gem.Amtes': int})

        # Create a simple lookup table to translate a plz to a gcd
        # there is a one to many relation from plz to gcd, but the exact assignment is usually identifyable using the ortsname
        # the self.gemeindeliste_pd is also filtered and cleaned in the _get_plz_lookup_dict method
        self.plz2gcd_dict = self._get_plz_lookup_dict()

        ################################### Anlagenregister #################################
        ###                                                                               ###
        ### The file 'anlagenregister.feather' contains the data from the Anlagenregister ###
        ###                                                                               ###
        #####################################################################################
        
        self.raw_combined_dataset = dataset / Path("raw-excel-e-control-data.feather")
        self.database_path = dataset / Path("anlagenregister.feather")

        e_control_data = dataset / Path("e-control-data")
        if not self.database_path.exists():
            # If the raw data file does not exist, create it
            if not self.raw_combined_dataset.exists():
                self._create_raw_data(e_control_data, self.raw_combined_dataset)
                assert self.raw_combined_dataset.exists(), f"Could not create the raw data file {self.raw_combined_dataset}."
            
            # Load the raw data from the Anlagenregister
            combined_raw_df = pd.read_feather(self.raw_combined_dataset)
            clean_df = self._filter_raw_data(combined_raw_df)
            
            # save the combined dataframe to a feather file
            clean_df.to_feather(self.database_path)
            self.database = pd.read_feather(self.database_path)
        else:
            self.database = pd.read_feather(self.database_path)

        # get the sum of energy production per Gemeinde
        self.photovoltaic_production_by_gcd = self._district_energy_sum()

        return
    

    def _filter_raw_data(self, combined_raw_df):
        # create a df with the same columns as the raw data, but add 'gcd' column
        clean_df_list = []
        
        # filter only "Photovoltaik" technology
        combined_raw_df = combined_raw_df[combined_raw_df['Technologie'] == 'Photovoltaik']
        for index, row in tqdm(combined_raw_df.iterrows(), total=len(combined_raw_df.index)):
            plz = row['Plz']
            ort = row['Ort']
            result = self._plz2gcd(plz, row)
            
            if result is None:
                print(Fore.YELLOW + f"Could not find a Gemeinde Code for PLZ {plz} and Ort {ort}." + Fore.RESET)
                continue
            else:
                gcd, actual_ort = result
  
            clean_row_dict = row.to_dict()
            clean_row_dict['gcd'] = gcd
            clean_row_dict['ort laut gemeindeliste'] = actual_ort
            clean_df_list.append(clean_row_dict)            

        clean_df = pd.DataFrame(clean_df_list)

        return clean_df


    def _get_plz_lookup_dict(self):

        ######## PREPROCESSING ########

        # drop all rows with NaN values in the 'Gemeinde code' column
        self.gemeindeliste_pd = self.gemeindeliste_pd.dropna(subset=['Gemeinde code'])
        self.gemeindeliste_pd = self.gemeindeliste_pd.dropna(subset=['PLZ des Gem.Amtes'])
        # convert the 'Gemeinde code' and 'PLZ des Gem.Amtes' columns to int
        self.gemeindeliste_pd['Gemeinde code'] = self.gemeindeliste_pd['Gemeinde code'].astype(int)
        self.gemeindeliste_pd['PLZ des Gem.Amtes'] = self.gemeindeliste_pd['PLZ des Gem.Amtes'].astype(int)
        
        # convert 'weitere Postleitzahlen' into list from space separated string, use loc to avoid SettingWithCopyWarning
        self.gemeindeliste_pd['weitere Postleitzahlen'] = self.gemeindeliste_pd['weitere Postleitzahlen'].apply(lambda x: x.split(" ") if type(x) == str else x)
        # convert list elements of 'weitere Postleitzahlen' into list of integers
        self.gemeindeliste_pd['weitere Postleitzahlen'] = self.gemeindeliste_pd['weitere Postleitzahlen'].apply(lambda x: [int(y) for y in x] if type(x) == list else x)

        ######## CREATE DICTIONARY ########

        # create a dictionary to quickly convert PLZ to Gemeinde code, we need 'Gemeinde code' and 'weitere Postleitzahlen' columns
        plz2gcd_dict = {}
        for index, row in self.gemeindeliste_pd.iterrows():
            plz = row['PLZ des Gem.Amtes']
            gcd = row['Gemeinde code']
            ort = row['Gemeindename']
            weitere_postleitzahlen = row['weitere Postleitzahlen']
            if plz in plz2gcd_dict:
                plz2gcd_dict[plz]['Gemeinde code'].append(gcd)
                plz2gcd_dict[plz]['ort'].append(ort)
                if type(weitere_postleitzahlen) == list:
                    # append all elements of 'weitere Postleitzahlen' to the list
                    plz2gcd_dict[plz]['weitere Postleitzahlen'].extend(weitere_postleitzahlen)
            else:
                plz2gcd_dict[plz] = {'Gemeinde code': list(), 'ort': list(), 'weitere Postleitzahlen': list()}
                plz2gcd_dict[plz]['Gemeinde code'].append(gcd)
                plz2gcd_dict[plz]['ort'].append(ort)
                if type(weitere_postleitzahlen) == list:
                    # append all elements of 'weitere Postleitzahlen' to the list
                    plz2gcd_dict[plz]['weitere Postleitzahlen'].extend(weitere_postleitzahlen)
        return plz2gcd_dict


    def _create_raw_data(self, e_control_data: Path, save_path: Path):
        """
        Load the raw data from the Anlagenregister
        """
        # Load the raw data from the Anlagenregister
        styria = pd.read_excel(e_control_data / Path("styria.xlsx"))
        tyrol = pd.read_excel(e_control_data / Path("tyrol.xlsx"))
        vienna = pd.read_excel(e_control_data / Path("vienna.xlsx"))
        vorarlberg = pd.read_excel(e_control_data / Path("vorarlberg.xlsx"))
        upper_austria = pd.read_excel(e_control_data / Path("upper_austria.xlsx"))
        salzburg = pd.read_excel(e_control_data / Path("salzburg.xlsx"))
        burgenland = pd.read_excel(e_control_data / Path("burgenland.xlsx"))
        carinthia = pd.read_excel(e_control_data / Path("carinthia.xlsx"))
        lower_austria = pd.read_excel(e_control_data / Path("lower_austria.xlsx"))

        combined_raw_df = pd.concat([styria, tyrol, vienna, vorarlberg, upper_austria, salzburg, lower_austria, burgenland, carinthia], ignore_index=True)
        # save to database
        combined_raw_df.to_feather(save_path)

        return
            

    
    def _plz2gcd(self, plz, row):
        """
        Convert a PLZ to a GCD

        Parameters:
        plz: int
            The PLZ to convert to a GCD
        row: pd.Series
            The row of the dataframe containing the PLZ and Ort

        Returns:
        tuple (int, str)
            The GCD and the Ort
        """
        
        #######################################
        ### First try to get the Plz as int ###
        #######################################
        ort = row['Ort']
        try:
            plz = int(plz)
        except:
            # Fix case where the PLZ prefix is 'A-'. We remove the 'A-' prefix.
            if len(str(plz).split('A-')) > 1:
                #print(Fore.GREEN + f"Found A- prefix in {plz} and splitting it." + Fore.RESET)
                plz = int(plz.replace("A-", ""))
            # Fix case where the PLZ prefix is 'A '. We remove the 'A ' prefix.
            elif len(str(plz).split('A ')) > 1:
                #print(Fore.GREEN + f"Found A prefix in {plz} and splitting it." + Fore.RESET)
                plz = int(plz.replace("A ", ""))
            # Fix the case where Plz is '<Plz> <Ortsname>'
            elif len(str(plz).split(' ')) > 1:
                    plz, ort = plz.split(' ')
                    plz = int(plz)
                    # print(Fore.GREEN + f"Splitting {plz} and {ort}" + Fore.RESET)
                    # print(combined_raw_df.loc[index])
            # Skip the case where the PLZ None. We cannot work with undefined PLZs.
            elif plz is None:
                # print(Fore.GREEN + f"Skipping None value for bundesland {row['Bundesland']}" + Fore.RESET)
                return None
            # Fix the case where PLZ and Ort are interchanged
            else:
                try:
                    ort = int(ort)
                    plz, ort = ort, plz
                    # print(Fore.GREEN + f"Swapping PLZ and Ort in {plz} and {ort}" + Fore.RESET)
                except:
                    return None
                    # print(Fore.RED + f"Could not convert {plz} to int." + Fore.RESET)

        ############################################
        ###  Then try to find the Gemeinde code  ###
        ############################################

        # get the Gemeinde code from the dictionary
        if plz in self.plz2gcd_dict:
            plz_info = self.plz2gcd_dict[plz]
            if len(plz_info['Gemeinde code']) > 1:                
                possible_orte = plz_info['ort']
                # find the closest match between the ort and possible_orte
                # use the Levenshtein distance to find the closest match of Ort
                max_distance = -np.inf
                for i, possible_ort in enumerate(possible_orte):
                    distance = fuzz.ratio(ort, possible_ort)
                    #print(f"Distance between {ort} and {possible_ort} is {distance}")
                    if distance > max_distance:
                        max_distance = distance
                        max_index = i
                final_ort = possible_orte[max_index]
                gcd = plz_info['Gemeinde code'][max_index]
                # print(f'found conflict for ort {ort} and dict {plz_info}, determined ORT {final_ort}')
            else:
                final_ort = plz_info['ort'][0]
                gcd = plz_info['Gemeinde code'][0]
                return gcd, final_ort
        else:
            # if we cannot find the plz in the plz columns, we need to find them in the 'weitere Postleitzahlen' column
            found_gemeinden = []
            for index, row in self.gemeindeliste_pd.iterrows():
                if row['weitere Postleitzahlen'] is np.nan:
                    continue
                elif plz not in row['weitere Postleitzahlen']:
                    continue
                else:
                    found_gemeinden.append(row.to_dict())

            if len(found_gemeinden) == 0:
                return None
            elif len(found_gemeinden) == 1:                
                final_ort = found_gemeinden[0]['Gemeindename']
                gcd = found_gemeinden[0]['Gemeinde code']
            elif len(found_gemeinden) > 1:
                # get the item with largest ratio between the ort and the all matches
                max_distance = -np.inf
                for i, possible_match in enumerate(found_gemeinden):
                    possible_ort = possible_match['Gemeindename']
                    distance = fuzz.ratio(ort, possible_ort)
                    if distance > max_distance:
                        max_distance = distance
                        max_index = i

                final_ort = found_gemeinden[max_index]['Gemeindename']
                gcd = found_gemeinden[max_index]['Gemeinde code']
        assert type(plz) == int, f"Expected plz to be int, got {type(plz)}."
        assert type(gcd) == int, f"Expected gcd to be int, got {type(gcd)}."
        return gcd, final_ort
            

    def _district_energy_sum(self):
        """
        Sum the energy production per district, specifically per Gemeindecode
        """
        # sum up all columns with same value for 'gcd' key in self.database
        # only sum up the columns with 'Eingespeister Strom' in the name
        sum_df = self.database.groupby('gcd').agg({col: 'sum' for col in self.database.columns if ('Eingespeister Strom' in col or 'Engpassleistung' in col)})
        # extract the index as a column
        sum_df.reset_index(inplace=True)

        # get the Gemeindename from the 'gcd' column
        sum_df['Gemeindename'] = sum_df['gcd'].apply(lambda x: self.gemeindeliste_pd[self.gemeindeliste_pd['Gemeinde code'] == x]['Gemeindename'].values[0])

        # add PLZ to the dataframe
        sum_df['PLZ'] = sum_df['gcd'].apply(lambda x: self.gemeindeliste_pd[self.gemeindeliste_pd['Gemeinde code'] == x]['PLZ des Gem.Amtes'].values[0])

        # for each column that contains 'Eingespeister Strom' in the name, convert the value to log10 scale
        for col in sum_df.columns:
            if 'Eingespeister Strom' in col:
                sum_df[col + ' log'] = np.log10(sum_df[col] + 1)

        # print(sum_df.head())
        # import sys; sys.exit(0)
        
        return sum_df


    def print_austria(self):

        # get the maximum for coloring the map
        # data_string = "Eingespeister Strom (kWh) 2024"
        # data_string = "Eingespeister Strom (kWh) 2023"
        #data_string = "Eingespeister Strom (kWh) 2022"
        data_string = "Eingespeister Strom (kWh) 2021"
        #data_string = "Eingespeister Strom (kWh) 2020"
        #data_string = "Eingespeister Strom (kWh) 2019"

        color_threshold = self.photovoltaic_production_by_gcd[data_string].quantile(0.98)


        fig = px.choropleth_mapbox(self.photovoltaic_production_by_gcd, geojson=self.gemeinden_austria_geojson, locations='gcd', color=data_string,
                                color_continuous_scale="Viridis",
                                range_color=(0, color_threshold),
                                mapbox_style="carto-positron",
                                zoom=6, center = {"lat": 47.69, "lon": 13.34},
                                opacity=0.5,
                                labels={data_string: data_string}
                                )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.show()
    

def main():
    this_file = Path(__file__).parent.resolve()
    dataset = this_file / Path("..", "dataset")
    anlagenregister = Anlagenregister(dataset)
    anlagenregister.print_austria()

    import sys; sys.exit(0)

    gemindecode = anlagenregister._plz2gcd(1190)
    print(gemindecode)

    for index, row in anlagenregister.database.iterrows():
        plz = row['Plz']
        print(f"PLZ: {type(plz)}")
        break
        if index > 10:
            break
if __name__ == "__main__":
    main()