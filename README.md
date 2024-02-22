# Super Easy Transformation of OSM Mapfiles to Garmin GPI

## Prerequisites
you will have to install the follwing external tools:
-  [`osmosis`](https://github.com/openstreetmap/osmosis)
-  [`gpsbabel`](https://github.com/GPSBabel/gpsbabel)

- the script `filter_nodes.py` has to be located in the same directory as your `*.pbf` map file. This is going to be your `working directory`

## Steps to use:

#### 1. Download desired area as `*.pbf` mapfile from https://extract.bbbike.org/
#### 2. Set your `pbf_file_name`
#### 3. Customize `POIs.yaml`:
- Define POI categories
- Define a radius (in meter) around each POI in which other POIs of the same category are deleted. Set this to a really really large number to keep all POIs
- Define `key`s and `values`s of [Map Features](https://wiki.openstreetmap.org/wiki/Map_features) that you want extract from the map
#### 4. Download POI-Icons as `*.bmp` (for example from [this](https://www.pocketnavigation.de/poidownload/pocketnavigation/de/?device-format-id=4&country=DE#selection-step2) website)
- The icons have to be named the same as the categories and be placed into `{working_path}/Icons`
#### 5. Run the script `filter_nodes.py`
#### Done!
