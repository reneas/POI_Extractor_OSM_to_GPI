from haversine import haversine, Unit
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import sys
import subprocess
import yaml
import argparse


# TODO add output format argument (gpi, csv, etc.)
def get_default_pbf_file():
    # Get the directory of the script
    script_dir = Path(__file__).parent
    # Find the first *.pbf file in the script directory
    for pbf_file in script_dir.glob("*.pbf"):
        return str(pbf_file)


# Create the parser
parser = argparse.ArgumentParser(
    description="Commandline tool for filtering OSM nodes from *.pbf files and converting them to GPI files for Garmin GPS devices."
)
# Add an argument for the PBF file
parser.add_argument(
    "-pbf",
    metavar="<*.pbf file>",
    default=get_default_pbf_file(),
    help="the *.pbf file to process",
)
parser.add_argument(
    "-f",
    metavar="<True/False>",
    default=False,
    help=f"Activate node filtering (default: {False})",
)
# Parse the arguments
args = parser.parse_args()


#################### FUNCTIONS ####################
def run_subprocess(command):
    command_name = command.split()[0]  # Get the name of the command
    print(f"Running {command_name} with command:\n{str(command)}\n")
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )
    output, _ = process.communicate()
    if process.returncode != 0:  # If the subprocess failed
        print(f"\033[1m\033[31m\033[4m{command_name} Error:\033[0m\n{output.decode()}")
        print(
            f"\033[1m\033[31m\033[4m{command_name} failed with exit code {process.returncode}\033[0m"
        )
        sys.exit(1)  # Stop the script with a non-zero exit code
    else:
        if command_name == "osmosis":
            print(f"{command_name} output:\n{output.decode()}")
            print(f"\033[1m\033[32m{command_name} finished successfully\033[0m")
        elif command_name == "gpsbabel":
            print(f"\033[1m\033[32m{command_name} finished successfully\033[0m")
    return process.returncode


def create_directory(path):
    """
    Create a directory and it's parents if they don't exist
    """
    if not path.exists():
        print(f"Creating directory: {path}\n")
        path.mkdir(parents=True)


def extract_nodes(pbf_file, poi, poi_dict, working_path):
    osm_raw_path = working_path / "osm_raw"
    create_directory(osm_raw_path)
    osmosis_command = f"""
    osmosis \\
        --read-pbf {pbf_file}\\
        --node-key-value keyValueList={poi_dict[poi][1]} \\
        --write-xml {osm_raw_path}/{poi}.osm"""
    exit_status = run_subprocess(osmosis_command)
    if exit_status == 0:  # If the subprocess was successful
        print(f'Successfully extracted "{poi}" nodes to {osm_raw_path}/{poi}.osm\n')
    else:  # If the subprocess failed
        print(
            f'\033[1m\033[31m\033[4mFailed to extract "{poi}" nodes. Check the error message above.\033[0m\n'
        )


def filter_nodes(xml_file, dist):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    nodes = []
    print(f"Filtering out nodes within {dist} meters...")
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
    print(f"Writing filtered nodes to {osm_filtered_path}/filtered_{poi}.osm...\n")
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


def create_gpi(working_path, inputdir, poi):
    iconpath = working_path / "Icons"
    gpipath = working_path / "GPI"
    create_directory(gpipath)
    if inputdir == "osm_filtered":
        osm_filtered_path = working_path / inputdir
        gpsbabel_command = f"""
        gpsbabel \\
            -i osm \\
            -f {osm_filtered_path}/filtered_{poi}.osm \\
            -o garmin_gpi,category={poi},bitmap={iconpath}/{poi}.bmp \\
            -F {gpipath}/{poi}.gpi"""

    else:
        osm_raw_path = working_path / inputdir
        gpsbabel_command = f"""
        gpsbabel \\
            -i osm \\
            -f {osm_raw_path}/{poi}.osm\\
            -o garmin_gpi,category={poi},bitmap={iconpath}/{poi}.bmp\\
            -F {gpipath}/{poi}.gpi"""
    exit_status = run_subprocess(gpsbabel_command)
    if exit_status == 0:
        print(f"Created {gpipath}/{poi}.gpi\n")
    else:
        print(f"\033[1m\033[31m\033[4mFailed to create {gpipath}/{poi}.gpi\033[0m\n")


def main():
    working_path = Path(__file__).parent
    pbf_file_name = args.pbf
    print(f"\nProcessing {pbf_file_name}...\nFiltering is set to {args.f}\n")
    with open("POIs.yaml", "r") as poi_file:
        poi_dict = yaml.safe_load(poi_file)

    for poi in poi_dict:
        if args.f:  # If filtering is activated
            extract_nodes(pbf_file_name, poi, poi_dict, working_path)
            filtered_nodes = filter_nodes(
                f"{working_path}/osm_raw/{poi}.osm", poi_dict[poi][0]
            )
            write_xml(
                filtered_nodes,
                working_path,
                poi,
            )
            create_gpi(working_path, "osm_filtered", poi)
        else:
            extract_nodes(pbf_file_name, poi, poi_dict, working_path)
            create_gpi(working_path, "osm_raw", poi)


if __name__ == "__main__":
    main()
