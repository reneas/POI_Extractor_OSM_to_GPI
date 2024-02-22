# Super Easy Transformation of OSM Mapfiles to Garmin GPI

## Prerequisites
you will have to install the follwing external tools:
-  [`osmosis`](https://github.com/openstreetmap/osmosis)
-  [`gpsbabel`](https://github.com/GPSBabel/gpsbabel)

## Steps to use:

#### 1. Download desired area as `*.pbf` mapfile from https://extract.bbbike.org/
#### 2. Set your `working_path` and `pbf_file_name`
- `working_path` is the directory where your `*.pbf` file is located
#### 3. Customize `poi_dict`:
- Define POI categories
- Define a radius (in meter) around each POI in which other POIs of the same category are deleted. Set this to a really really large number to keep all POIs
- Define `key`s and `values`s of [Map Features](https://wiki.openstreetmap.org/wiki/Map_features) that you want extract from the map
#### 4. Download POI-Icons as `*.bmp` (for example from [this](https://www.pocketnavigation.de/poidownload/pocketnavigation/de/?device-format-id=4&country=DE#selection-step2) website)
- The icons have to be named the same as the categories and be placed into `{working_path}/Icons`
#### 5. Run the script `filter_nodes.py`
#### Done!
