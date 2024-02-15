import pandas as pd
import geopandas as gp
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from searvey.coops import get_coops_stations
from searvey import ioc
from gesla import GeslaDataset

PROVIDERS = { 
    'gesla3_id': 'filename', 
    'ioc_id': 'ioc_code', 
    'coops_id': 'nws_id' , 
    'emodnet_id': 'platform_code', 
    'cmems_id': 'PLATFORM_CODE'
    }
PLOT = False

def drop_geometry(df):
    df['longitude'] = df['geometry'].x
    df['latitude'] = df['geometry'].y
    return df.drop('geometry',axis=1)


def detect_new_stations(ref_df,provider_key, df, plot = False): 
    id = PROVIDERS[provider_key]
    existing_rows = ref_df[ref_df[id].isin(df[id])]
    if plot: 
        fig, ax = plt.subplots(figsize=(20,10))
        ax.set_title(provider_key)
        countries = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        countries.plot(color='lightgrey', ax=ax, zorder=-1)
        ref_df.plot.scatter(ax=ax, x='longitude',y='latitude',s=30, label = 'reference catalog')
        df[~df[id].isin(existing_rows[id])].plot.scatter(ax=ax, x='longitude',y='latitude', c='r',s=20, label='new stations')
        df.plot.scatter(ax=ax, x='longitude',y='latitude', c='y',s=2,label='last API call')
        plt.tight_layout()
        plt.show()
    return df[~df[id].isin(existing_rows[id])]     # New stations not in the reference catalog


def calculate_distance(lat1, lon1, lat2, lon2):
    # Approximate radius of earth in km
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    return np.sqrt(dlon**2 + dlat**2)


def append_or_warn(ref_df, new_df, provider_key):
    """
    For each station in new_df, check if it exists in ref_df based on Station_Name.
    If it exists and the provider is not listed, update the entry.
    If it exists and the provider is listed, print a warning.
    If it does not exist, append it with a new seaset_id.
    """
    for index, new_row in new_df.iterrows():
        # 1. test on ids 
        #    names might not be the same but specific providers id codes will always remain
        id = PROVIDERS[provider_key]
        existing_rows = ref_df[ref_df[id].isin([new_row[id]])]

        # 2. test on distances
        distances = calculate_distance(
            ref_df['latitude'], ref_df['longitude'],
            new_row['latitude'], new_row['longitude']
        )
        min_distance = distances.min()
        closest_station_index = distances.idxmin()
        is_close = min_distance <= 10e-4 # station within 10m

        if not existing_rows.empty:
            # Check if the provider is already listed for this station
            existing_provider = existing_rows[provider_key].notnull().any()
            if existing_provider:
                # If provider is listed, print warning
                print(f"Warning: provider already listed: {new_row[id]}")
            else:
                # If provider is not listed, append provider info to the existing seaset_id
                ref_df.loc[ref_df[provider_key] == new_row[id], provider_key] = new_row[id]
        elif is_close: 
            existing_row = ref_df.loc[closest_station_index]
            if existing_row[provider_key] == new_row[id]:
                # provider is listed: it shouldn't happen if first test is sucessful
                raise ValueError(f"Error: Duplicate station with provider already listed: {new_row[id]}")
            else:
                # If provider is not listed, append provider info to the existing seaset_id
                for prov in PROVIDERS.keys():
                    if not pd.isna(ref_df.at[closest_station_index, prov]):
                        print(' > data existing for', prov, " >> ", ref_df.at[closest_station_index, prov])
                for col in new_row.index:
                    # replacing ONLY nans with new values
                    if pd.isna(ref_df.at[closest_station_index, col]):
                        ref_df.at[closest_station_index, col] = new_row[col]
        else:
            # If no duplicate, append new station with a new seaset_id
            new_seaset_id = ref_df['seaset_id'].max() + 1
            new_row['seaset_id'] = new_seaset_id
            new_row[provider_key] = new_row.Station_Name
            if new_row.notna().any():
                # If yes, proceed with concatenation
                ref_df = pd.concat([ref_df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                # Optional: handle the case where new_row is entirely NA (e.g., log a message)
                print("Skipped adding a row with all NA values.")
            # ref_df = pd.concat([ref_df, pd.DataFrame([new_row])], ignore_index=True)
            
    return ref_df


def main():
    # Load the original reference catalog
    ref_ = pd.read_csv('catalog_full.csv', index_col=0)
        
    # COOPS
    coops = get_coops_stations()
    coops = drop_geometry(coops)
    coops = coops.rename(columns={'name': 'Station_Name'})
    new_coops = detect_new_stations(ref_, 'coops_id', coops, plot = PLOT)
    ref1 = append_or_warn(ref_, new_coops, 'coops_id')
    # IOC
    ioc_stations = ioc.get_ioc_stations()
    ioc_stations = ioc_stations.rename(columns={'lon':'longitude','lat':'latitude', 'country': 'Country', 'location': 'Station_Name'})
    ioc_stations = drop_geometry(ioc_stations)
    ioc_stations = ioc_stations.drop_duplicates(subset=['ioc_code'])
    new_ioc = detect_new_stations(ref_, 'ioc_id', ioc_stations, plot = PLOT)
    ref1 = append_or_warn(ref1, new_ioc, 'ioc_id')
    # EMODNET
    emodnet = pd.read_csv('emodnet.csv')
    emodnet = emodnet.rename(columns={'longitude (degrees_east)':'longitude','latitude (degrees_north)':'latitude'})
    emodnet = emodnet.drop_duplicates(['EP_PLATFORM_CODE'])
    emodnet[~emodnet.EP_PLATFORM_ID.isna()]
    new_emodnet = detect_new_stations(ref_, 'emodnet_id', emodnet, plot = PLOT)
    ref1 = append_or_warn(ref1, new_emodnet, 'emodnet_id')
    # CMEMS
    cmems = pd.read_csv('cmems.csv')
    cmems = cmems.rename(columns={'longitude (degrees_east)':'longitude','latitude (degrees_north)':'latitude', 'PLATFORM_NAME': 'Station_Name'})
    cmems = cmems.drop(cmems.columns[0],axis=1)
    cmems = cmems.drop_duplicates()
    new_cmems = detect_new_stations(ref_, 'cmems_id', cmems, plot = PLOT)
    ref1 = append_or_warn(ref1, new_cmems, 'cmems_id')
    ref1.to_csv('catalog_full_updated.csv')

    # Save the updated catalog
    ref1.to_csv('catalog_full_updated.csv')

if __name__ == "__main__":
    main()