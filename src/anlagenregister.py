import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as  np
import json
import subprocess
from tqdm import tqdm
from rapidfuzz import fuzz
from colorama import Fore


class Anlagenregister():
    """
    Class to load & display the data from the Anlagenregister
    """
    def __init__(self, dataset: Path):
        # Load your GeoJSON data (replace 'austria_districts.geojson' with your filename)
        this_file = Path(__file__).parent.resolve()
        self.austria_simplifyed = this_file / Path("..", "third_party", "GeoJSON-TopoJSON-Austria", "2021", "simplified-99.5", "gemeinden_995_geo.json")

        
        ################################# Gemeindeliste ################################
        ###                                                                          ###
        ### The file 'gemliste_knz.xls' contains a mapping from PLZ to Gemeinde code ###
        ###                                                                          ###
        ################################################################################

        plz_conversion_path = (dataset / Path("gemliste_knz.xls")).resolve()
        assert plz_conversion_path.exists(), f"The file {plz_conversion_path} does not exist."
        self.plz2gkz = pd.read_excel(plz_conversion_path, skiprows=3)#, dtype={'Gemeinde code': int, 'PLZ des Gem.Amtes': int})

        # show how many NaN values are in the 'Gemeinde code' column
        # print(self.plz2gkz['Gemeinde code'].isna().sum())
        # print(self.plz2gkz['PLZ des Gem.Amtes'].isna().sum())

        # drop all rows with NaN values in the 'Gemeinde code' column
        self.plz2gkz = self.plz2gkz.dropna(subset=['Gemeinde code'])
        self.plz2gkz = self.plz2gkz.dropna(subset=['PLZ des Gem.Amtes'])
        # convert the 'Gemeinde code' and 'PLZ des Gem.Amtes' columns to int
        self.plz2gkz['Gemeinde code'] = self.plz2gkz['Gemeinde code'].astype(int)
        self.plz2gkz['PLZ des Gem.Amtes'] = self.plz2gkz['PLZ des Gem.Amtes'].astype(int)
        
        # convert 'weitere Postleitzahlen' into list from space separated string, use loc to avoid SettingWithCopyWarning
        self.plz2gkz['weitere Postleitzahlen'] = self.plz2gkz['weitere Postleitzahlen'].apply(lambda x: x.split(" ") if type(x) == str else x)
        # convert list elements of 'weitere Postleitzahlen' into list of integers
        self.plz2gkz['weitere Postleitzahlen'] = self.plz2gkz['weitere Postleitzahlen'].apply(lambda x: [int(y) for y in x] if type(x) == list else x)

        # create a dictionary to quickly convert PLZ to Gemeinde code, we need 'Gemeinde code' and 'weitere Postleitzahlen' columns
        self.plz2gkz_dict = {}
        for index, row in self.plz2gkz.iterrows():
            plz = row['PLZ des Gem.Amtes']
            kgz = row['Gemeinde code']
            ort = row['Gemeindename']
            weitere_postleitzahlen = row['weitere Postleitzahlen']
            if plz in self.plz2gkz_dict:
                self.plz2gkz_dict[plz]['Gemeinde code'].append(kgz)
                self.plz2gkz_dict[plz]['ort'].append(ort)
                if type(weitere_postleitzahlen) == list:
                    # append all elements of 'weitere Postleitzahlen' to the list
                    self.plz2gkz_dict[plz]['weitere Postleitzahlen'].extend(weitere_postleitzahlen)
                # print(f"Found duplicate Ort {self.plz2gkz_dict[plz]}")
            else:
                self.plz2gkz_dict[plz] = {'Gemeinde code': list(), 'ort': list(), 'weitere Postleitzahlen': list()}
                self.plz2gkz_dict[plz]['Gemeinde code'].append(kgz)
                self.plz2gkz_dict[plz]['ort'].append(ort)
                if type(weitere_postleitzahlen) == list:
                    # append all elements of 'weitere Postleitzahlen' to the list
                    self.plz2gkz_dict[plz]['weitere Postleitzahlen'].extend(weitere_postleitzahlen)
                    # print(self.plz2gkz_dict[plz])

        
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
            combined_df = pd.read_feather(self.raw_combined_dataset)

            indices_to_drop = []
            for index, row in tqdm(combined_df.iterrows()):
                plz = row['Plz']
                ort = row['Ort']
                gkz = self._plz2gkz(plz, combined_df, index, row)
                if gkz is None:
                    indices_to_drop.append(index)
                    print(Fore.RED + f"Could not find a Gemeinde Code for PLZ {plz} and Ort {ort}." + Fore.RESET)
                    continue
                continue
                print(f"PLZ: {plz}, Ort: {ort}, GKZ: {gkz}")
                import sys; sys.exit(0)
                # Filter out rows with 2 NaN values
                # if pd.isna(plz) and pd.isna(ort):
                #     print(f"Found row with 2 NaN values in row {index}")
                #     continue

                # Fix case where the PLZ prefix is 'A-'. We remove the 'A-' prefix.
                # if type(plz) == str:
                #     plz = plz.replace("A-", "").replace("A ", "")

                try:
                    plz = int(plz)
                except ValueError:
                    # Fix the case where PLZ and Ort are interchanged
                    try:
                        ort = int(ort)
                        plz, ort = ort, plz
                        combined_df.loc[index, 'Plz'] = plz
                        combined_df.loc[index, 'Ort'] = ort
                    except ValueError:
                        pass
                            
                try:
                    plz = int(plz)
                    #combined_df.iloc[index]['Plz'] = plz
                    combined_df.loc[index, 'Plz'] = plz
                except ValueError:
                    #print(f"Found value in row {index} with PLZ {plz} and ort {ort}")
                    indices_to_drop.append(index)
                    continue
                # replace the ort and plz values with the cleaned up values
                row['Plz'] = plz
                row['Ort'] = ort
                #clean_df.loc[len(clean_df)] = row
            import sys; sys.exit(0)

            
            # drop all rows in indices_to_drop
            print(f"Dropping {len(indices_to_drop)} rows.")
            combined_df.drop(indices_to_drop, inplace=True)
            # save the combined dataframe to a feather file
            combined_df.to_feather(self.database_path)
            self.database = pd.read_feather(self.database_path)
        else:
            self.database = pd.read_feather(self.database_path)
            # print the set of all 'Bundesland' values


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

        combined_df = pd.concat([styria, tyrol, vienna, vorarlberg, upper_austria, salzburg, lower_austria, burgenland, carinthia], ignore_index=True)
        # save to database
        combined_df.to_feather(save_path)

        return
            

    
    def _plz2gkz(self, plz, combined_df, index, row):
        """
        Convert a PLZ to a GKZ
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
                    combined_df.loc[index, 'Plz'] = plz
                    # print(Fore.GREEN + f"Splitting {plz} and {ort}" + Fore.RESET)
                    # print(combined_df.loc[index])
            # Skip the case where the PLZ None. We cannot work with undefined PLZs.
            elif plz is None:
                # print(Fore.GREEN + f"Skipping None value for bundesland {row['Bundesland']}" + Fore.RESET)
                return None
            # Fix the case where PLZ and Ort are interchanged
            else:
                try:
                    ort = int(ort)
                    plz, ort = ort, plz
                    combined_df.loc[index, 'Plz'] = plz
                    combined_df.loc[index, 'Ort'] = ort
                    # print(Fore.GREEN + f"Swapping PLZ and Ort in {plz} and {ort}" + Fore.RESET)
                except:
                    return None
                    # print(Fore.RED + f"Could not convert {plz} to int." + Fore.RESET)
                    #print(row) 


        ############################################
        ###  Then try to find the Gemeinde code  ###
        ############################################

        # get the Gemeinde code from the dictionary
        if plz in self.plz2gkz_dict:
            plz_info = self.plz2gkz_dict[plz]
            if len(plz_info['Gemeinde code']) > 1:
                #print(f"Found Gemeinde code {kgz} for PLZ {plz}")
                
                possible_orte = plz_info['ort']
                # find the closest match between the ort and possible_orte
                max_distance = -np.inf
                
                # use the Levenshtein distance to find the closest match of Ort
                for i, possible_ort in enumerate(possible_orte):
                    
                    distance = fuzz.ratio(ort, possible_ort)
                    #print(f"Distance between {ort} and {possible_ort} is {distance}")

                    if distance > max_distance:
                        max_distance = distance
                        max_index = i
                final_ort = possible_orte[max_index]
                # print(f'found conflict for ort {ort} and dict {plz_info}, determined ORT {final_ort}')
                # print()
        return 1
        import sys; sys.exit(0)

        result = self.plz2gkz[self.plz2gkz['PLZ des Gem.Amtes'] == plz]['Gemeinde code']
        n_hits = len(result)
        # If there is no hit in 'PLZ des Gem.Amtes' column, try the 'weitere Postleitzahlen' column
        # This column contains multiple PLZs separated by a space. One of them should match the PLZ
        if n_hits == 0:
            for index, row in self.plz2gkz.iterrows():
                weitere_postleitzahlen = str(row['weitere Postleitzahlen'])
                if str(plz) in weitere_postleitzahlen:
                    kgz = int(row['Gemeinde code'])
                    return kgz
            # If we did not find a match, return None
            return None
        # If there is only one hit, we take that one
        elif n_hits == 1:
            kgz = int(result.iloc[0])
        # If there are multiple hits, we take the first one
        elif n_hits > 1:
            kgz = int(result.iloc[0])
            #raise ValueError(f"Expected 1 Gemeinde Code for PLZ {plz}, got {n_hits}: \n{result}.")
        return kgz
    

    def print_austria(self):
        with open(self.austria_simplifyed) as f:
            austria_map = json.load(f)

        #number of districts
        # print(len(austria_map['features']))

        

        for i, elem in enumerate(austria_map['features']):
            elem["id"] = elem['properties']['iso']

        # create a df with the ids and a random value between 0 and 10
        df = pd.DataFrame({
            "fips": [int(elem['id']) for elem in austria_map['features']],
            "unemp": 0.0
            })
        
        for index, row in tqdm(self.database.iterrows(), total=len(self.database)):
            try:
                technology = row['Technologie']
                if technology != 'Photovoltaik':
                    continue
                plz = row['Plz']
                plz = int(plz)
                #print(f"PLZ: {plz}")
                gkz = self._plz2gkz(plz)
                if gkz is None:
                    #print(f"Could not find a GKZ for PLZ {plz}")
                    continue
                #print(f"GKZ: {gkz}")
                strom = int(row['Eingespeister Strom (kWh) 2024'])
                if strom == 0:
                    continue
                # prnint the df row where the fips is equal to gkz
                #print(df.loc[df['fips'] == gkz])
                df.loc[df['fips'] == gkz, 'unemp'] += strom
                #print(df.loc[df['fips'] == gkz])
                
            except:
                # print the error and continue
                print(f"Error in row {index}")
                print(row)
                df.loc[df['fips'] == gkz, 'unemp'] = strom
                import sys; sys.exit(0) 


        fig = px.choropleth_mapbox(df, geojson=austria_map, locations='fips', color='unemp',
                                color_continuous_scale="Viridis",
                                range_color=(0, 200000),
                                mapbox_style="carto-positron",
                                zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                                opacity=0.5,
                                labels={'unemp':'Energy Production 2024 [kwh]'}
                                )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.show()
    

def main():
    this_file = Path(__file__).parent.resolve()
    dataset = this_file / Path("..", "dataset")
    anlagenregister = Anlagenregister(dataset)
    anlagenregister.print_austria()
    import sys; sys.exit(0)
    gemindecode = anlagenregister._plz2gkz(1190)
    print(gemindecode)

    for index, row in anlagenregister.database.iterrows():
        plz = row['Plz']
        print(f"PLZ: {type(plz)}")
        break
        if index > 10:
            break
if __name__ == "__main__":
    main()