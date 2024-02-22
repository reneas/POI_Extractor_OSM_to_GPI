# Super Easy Transformation of OSM Mapfiles to Garmin GPI

## Prerequisites
you will have to install the follwing external tools:
-  [`osmosis`](https://github.com/openstreetmap/osmosis)
-  [`gpsbabel`](https://github.com/GPSBabel/gpsbabel)

- the script `filter_nodes.py` has to be located in the same directory as your `*.pbf` map file. This is going to be your `working_path`

## Steps to use:

#### 1. Download desired area as `*.pbf` mapfile from https://extract.bbbike.org/
#### 2. Customize `POIs.yaml`:
- Define POI categories
- Define a radius (in meter) around each POI in which other POIs of the same category are deleted. Set this to a really really large number to keep all POIs
- Define `key`s and `values`s of [Map Features](https://wiki.openstreetmap.org/wiki/Map_features) that you want extract from the map
#### 3. Download POI-Icons as `*.bmp` (for example from [this](https://www.pocketnavigation.de/poidownload/pocketnavigation/de/?device-format-id=4&country=DE#selection-step2) website)
- The icons have to be named the same as the categories and be placed into `{working_path}/Icons`
#### 4. Run the script with `python ./filter_nodes.py -pbf [pbf_file_name]` in your `working_path`
- You don't need to specify the `*.pbf` file if there is only one in the directory. The script will automatically choose the first `*.pbf` file in the directory, if there are more than one present and no `-pbf` argument was given.
#### Done!
