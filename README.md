# Super Easy Transformation of OSM Mapfiles to Garmin GPI

## Prerequisites
you will have to install the follwing external tools:
-  [`osmosis`](https://github.com/openstreetmap/osmosis)
-  [`gpsbabel`](https://github.com/GPSBabel/gpsbabel)

### "Installing"
- make `filter-nodes` executable
- move/copy it to a directory of your choice that is on your `PATH` or add your desired directory to your `PATH`
- now you can run it from anywhere using `filter-nodes`
- **NOTE:** the directory you're running the script from is going to be your `working_directory` 

## Steps to use:

#### 1. Download desired area as `*.pbf` mapfile from https://extract.bbbike.org/
#### 2. Customize `POIs.yaml`:
- The file has to be in your `working_path`
- Define POI categories
- Define a radius (in meter) around each POI in which other POIs of the same category are deleted. Set this to a really really large number to keep all POIs
- Define `key`s and `values`s of [Map Features](https://wiki.openstreetmap.org/wiki/Map_features) that you want extract from the map
#### 3. Download POI-Icons as `*.bmp` (for example from [this](https://www.pocketnavigation.de/poidownload/pocketnavigation/de/?device-format-id=4&country=DE#selection-step2) website)
- The icons have to be named the same as the categories and be placed into `{working_path}/Icons`
#### 4. Run the script with `filter-nodes` in your `working_path`
- You don't need to specify the `*.pbf` file if there is only one in the directory. The script will automatically choose the first `*.pbf` file in the directory, if there are more than one present and no `-pbf` argument was given.
#### Done!
