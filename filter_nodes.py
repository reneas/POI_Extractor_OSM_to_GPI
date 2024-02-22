from haversine import haversine, Unit
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import subprocess
import yaml
import argparse

# TODO: Make the script more flexible by using command line arguments

# Create the parser
parser = argparse.ArgumentParser(description="declare the PBF file to process")
# Add an argument for the PBF file
parser.add_argument(
    "-pbf",
    "--pbf_file",
    default="map_alpentour.pbf",
    help="The PBF file to process",
)
# Parse the arguments
args = parser.parse_args()


#################### FUNCTIONS ####################
def run_subprocess(command):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    output, error = process.communicate()
    if output:
        print("Output:", output.decode())
    if error:
        print("Error:", error.decode())


def create_directory(path):
    """
    Create a directory and it's parents if they don't exist
    """
    path.mkdir(parents=True, exist_ok=True)


def extract_nodes(pbf_file, poi, poi_dict, working_path):
    osm_raw_path = working_path / "osm_raw"
    create_directory(osm_raw_path)
    osmosis_command = f"osmosis --read-pbf {pbf_file} --node-key-value keyValueList={poi_dict[poi][1]} --write-xml {osm_raw_path}/{poi}.osm"
    print(osmosis_command)
    run_subprocess(osmosis_command)


def filter_nodes(xml_file, dist):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    nodes = []
    for node in root.findall("node"):
        lat = float(node.get("lat"))
        lon = float(node.get("lon"))
        if nodes:
            for n in nodes:
                if (
                    haversine((lat, lon), (n[0], n[1]), unit=Unit.METERS) < dist
                ):  # dist meters distance between nodes is allowed
                    # print(haversine((lat, lon), (n[0], n[1]), unit=Unit.METERS))
                    # print((lat, lon), (n[0], n[1]))
                    root.remove(node)
                    break
            else:
                nodes.append((lat, lon, node))
        else:
            nodes.append((lat, lon, node))
    return root


def write_xml(root, working_path, poi):
    osm_filtered_path = working_path / "osm_filtered"
    create_directory(osm_filtered_path)
    # Open the output file in write mode
    with open(f"{osm_filtered_path}/filtered_{poi}.osm", "w") as f:
        # Write the XML declaration
        f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        # Write the tree to a string
        xml_string = ET.tostring(root, encoding="utf-8", method="xml")
        # Decode bytes to string
        xml_string = xml_string.decode("utf-8")
        # Remove spaces before />
        xml_string = re.sub(" />", "/>", xml_string)
        # Write the modified XML string to the file
        f.write(xml_string)


def create_gpi(working_path, poi):
    iconpath = working_path / "Icons"
    gpipath = working_path / "GPI"
    osm_filtered_path = working_path / "osm_filtered"
    create_directory(gpipath)
    gpsbabel_command = f"gpsbabel -i osm -f {osm_filtered_path}/filtered_{poi}.osm -o garmin_gpi,category={poi},bitmap={iconpath}/{poi}.bmp -F {gpipath}/{poi}.gpi"
    print(gpsbabel_command)
    run_subprocess(gpsbabel_command)


def main():
    working_path = Path(__file__).parent
    pbf_file_name = args.pbf_file

    with open("POIs.yaml", "r") as poi_file:
        poi_dict = yaml.safe_load(poi_file)

    for poi in poi_dict:
        extract_nodes(f"{working_path}/{pbf_file_name}", poi, poi_dict, working_path)
        write_xml(
            filter_nodes(f"{working_path}/osm_raw/{poi}.osm", poi_dict[poi][0]),
            working_path,
            poi,
        )
        create_gpi(working_path, poi)


if __name__ == "__main__":
    main()
