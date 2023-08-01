# seaset


Seaset aims to provide the following functionality:

- Unified catalogue of observational data including near real time.
- Standarization of metadata across providers
- automatic updates

## Update 07/2023

- Update the Catalog Notebook; retrieving the latest version of searvey and merging also the GESLA3 Dataset
- Merged all the datasets into one table, fusioning also the parameters for duplicated rows= total number of stations: 6101 (7690 stations - 1589 duplicates). That can be found in catalog_new.csv
- Merged 2 projects: [searvey](https://github.com/oceanmodeling/searvey) and [GESLA3](https://github.com/philiprt/GeslaDataset). Also please go directly on the [GESLA3 website](https://gesla787883612.wordpress.com/downloads/) to download the their database (~5Gb compressed)
   - added the gesla.py script from https://github.com/philiprt/GeslaDataset
   - modified the gesla.py script to be able to select from a certain region of world
- added U_tide fonction for analysis of the tide constituents 