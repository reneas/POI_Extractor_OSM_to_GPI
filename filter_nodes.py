from haversine import haversine, Unit
import xml.etree.ElementTree as ET
import re
import os
import subprocess

# POIs
# "Camping"     300m
# "Fahrrad"     100m
# "Fastfood"    100m
# "Hotel"       200m
# "Hütte"       300m
# "Icecream"    100m
# "Picknick"    1000m
# "Supermarkt"  100m
# "Wasser"      150m

working_path ="/home/reneas/Dokumente/OSM/Alpentour"
pbf_file_name = "map_alpentour.pbf"

poi_dict = {
    "Camping": [300, 'tourism.camp_pitch,tourism.camp_site,tourism.caravan_site'],
    "Fahrrad": [100, 'amenity.bicycle_repair_station,shop.bicycle'],
    "Fastfood": [100, 'shop.bakery,amenity.fast_food'],
    "Hotel": [200, 'tourism.hostel,tourism.hotel,tourism.motel,tourism.apartment,tourism.guest_house'],
    "Hütte": [300, 'tourism.alpine_hut,tourism.wilderness_hut'],
    "Icecream": [100, 'amenity.ice_cream'],
    "Picknick": [1000, 'amenity.bench,leisure.picnic_table,tourism.picnic_site'],
    "Supermarkt": [100, 'shop.convenience,shop.supermarket,shop.food'],
    "Wasser": [150, 'emergency.drinking_water,amenity.drinking_water,natural.spring']
}

def extract_nodes(pbf_file, poi):
    if not os.path.exists(f'{working_path}/osm_raw'):
    # If the directory doesn't exist, create it
        os.makedirs(f'{working_path}/osm_raw')
    osmosis_command = f"osmosis --read-pbf {pbf_file} --node-key-value keyValueList={poi_dict[poi][1]} --write-xml {working_path}/osm_raw/{poi}.osm"
    print(osmosis_command)
    process = subprocess.Popen(osmosis_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    # Print the output and error messages, if any
    if output:
        print("Output:", output.decode())
    if error:
        print("Error:", error.decode())

def filter_nodes(xml_file, dist):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    nodes = []
    for node in root.findall('node'):
        lat = float(node.get('lat'))
        lon = float(node.get('lon'))
        if nodes:
            for n in nodes:
                if haversine((lat, lon), (n[0], n[1]), unit=Unit.METERS) < dist: # dist meters distance between nodes is allowed
                    # print(haversine((lat, lon), (n[0], n[1]), unit=Unit.METERS))
                    # print((lat, lon), (n[0], n[1]))
                    root.remove(node)
                    break
            else:
                nodes.append((lat, lon, node))
        else:
            nodes.append((lat, lon, node))
    return root

def write_xml(root, filtered_dir):
    if not os.path.exists(filtered_dir):
    # If the directory doesn't exist, create it
        os.makedirs(filtered_dir)
    # Open the output file in write mode
    with open(f"{filtered_dir}/filtered_{poi}.osm", 'w') as f:
        # Write the XML declaration
        f.write('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
        # Write the tree to a string
        xml_string = ET.tostring(root, encoding='utf-8', method="xml")
        # Decode bytes to string
        xml_string = xml_string.decode('utf-8')
        # Remove spaces before /> in empty tags
        xml_string = re.sub(' />', '/>', xml_string)
        # Write the modified XML string to the file
        f.write(xml_string)

def create_gpi():
    iconpath = f"{working_path}/Icons"
    gpipath = f"{working_path}/GPI"
    inputpath = f"{working_path}/osm_filtered"
    if not os.path.exists(gpipath):
    # If the directory doesn't exist, create it
        os.makedirs(gpipath)
    gpsbabel_command = f"gpsbabel -i osm -f {inputpath}/filtered_{poi}.osm -o garmin_gpi,category={poi},bitmap={iconpath}/{poi}.bmp -F {gpipath}/{poi}.gpi"
    print(gpsbabel_command)
    process = subprocess.Popen(gpsbabel_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    # Print the output and error messages, if any
    if output:
        print("Output:", output.decode())
    if error:
        print("Error:", error.decode())

for poi in poi_dict:
    filtered_dir = f"{working_path}/osm_filtered"
    extract_nodes(f"{working_path}/{pbf_file_name}", poi)    
    write_xml(filter_nodes(f'{working_path}/osm_raw/{poi}.osm', poi_dict[poi][0]), filtered_dir)
    create_gpi()