from haversine import haversine, Unit
from pathlib import Path
from multiprocessing import Pool
import multiprocessing
import xml.etree.ElementTree as ET
import re
import sys
import subprocess
import yaml
import argparse
import time


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
    default=get_default_pbf_file(),
    help="The *.pbf file to process. Default: Uses the alphabetically first *.pbf file in the script directory.",
)
parser.add_argument(
    "-f",
    action="store_false",
    help=f"Deactivate node filtering (default: Activated). If deactivated, all nodes will be extracted. If activated, nodes within a certain distance of each other will be filtered out. The distance is specified in the POIs.yaml file.",
)
parser.add_argument(
    "-m",
    action="store_true",
    help=f"Activate multiprocessing (default: Single-Core-Processing). Useful for large *.pbf files. This uses ALL YOUR CORES MINUS TWO! Note: Multiprocessing might not work on Windows. Use single processing if you encounter any issues.",
)
# Parse the arguments
args = parser.parse_args()


#################### FUNCTIONS ####################
def run_subprocess(command):
    command_name = command.split()[0]  # Get the name of the command
    print(f"Running {command_name} with command:\n{str(command)}\n")
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            check=True,
        )
        if command_name == "osmosis":
            print(f"{command_name} output:\n{result.stdout.decode()}")
        print(f"\033[1m\033[32m{command_name} finished successfully\033[0m")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(
            f"\033[1m\033[31m\033[4m{command_name} Error:\033[0m\n{e.output.decode()}"
        )
        if command_name == "osmosis":
            print(
                f"\033[1m\033[31m\033[4m{command_name} failed to extract nodes. Check the error message above.\033[0m\n"
            )
        elif command_name == "gpsbabel":
            print(
                f"\033[1m\033[31m\033[4m{command_name} failed to create GPI-File\033[0m\n"
            )
        sys.exit(1)  # Stop the script with a non-zero exit code


def create_directory(path):
    """
    Create a directory and its parents if they don't exist
    """
    try:
        if not path.exists():
            print(f"Creating directory: {path}\n")
            path.mkdir(parents=True)
    except PermissionError:
        print(f"Error: Permission denied when trying to create directory: {path}")
    except OSError as e:
        print(f"Error: Unable to create directory: {path}. Reason: {e.strerror}")


def extract_nodes(pbf_file, poi, poi_dict, working_path):
    try:
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
    except KeyError:
        print(f"Error: The POI '{poi}' is not found in the POI dictionary.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def filter_nodes(xml_file, dist):
    # TODO: Show how many nodes were filtered out in each node
    try:
        tree = ET.parse(xml_file)
    except ET.ParseError:
        print(f"Error: The file {xml_file} is not a well-formed XML file.")
        sys.exit(1)
    root = tree.getroot()
    nodes = []
    print(f"Filtering out nodes within {dist} meters...")
    for node in root.findall("node"):
        lat = float(node.get("lat"))
        lon = float(node.get("lon"))
        if nodes:
            for n in nodes:
                if haversine((lat, lon), (n[0], n[1]), unit=Unit.METERS) < dist:
                    root.remove(node)
                    break
            else:
                nodes.append((lat, lon, node))
        else:
            nodes.append((lat, lon, node))

        # Extract certain tags and write them into the node id
        # write the tags in the order of tag_order
        tag_order = ["amenity", "shop", "website", "opening_hours"]
        tags = [tag for tag in node.findall("tag") if tag.get("k") in tag_order]
        tags.sort(key=lambda tag: tag_order.index(tag.get("k")))
        # add a separator between the tags and every 35 chars inside one tag
        tag_values = []
        for tag in tags:
            tag_value = tag.get("v")
            for i in range(35, len(tag_value), 35):
                tag_value = tag_value[:i] + "\\" + tag_value[i:]
            tag_values.append(tag_value)
        node.set("id", "\\".join(tag_values))
    return root


def write_xml(root, working_path, poi):
    try:
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
            # Replace all '\' characters with '&#xA;'
            xml_string = xml_string.replace("\\", "&#xA;")
            # Remove spaces before />
            xml_string = re.sub(" />", "/>", xml_string)
            # Write the modified XML string to the file
            f.write(xml_string)
    except PermissionError:
        print(
            f"Error: Permission denied when trying to write to file: {osm_filtered_path}/filtered_{poi}.osm"
        )
    except OSError as e:
        print(
            f"Error: Unable to write to file: {osm_filtered_path}/filtered_{poi}.osm. Reason: {e.strerror}"
        )
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def create_gpi(working_path, inputdir, poi):
    try:
        iconpath = working_path / "Icons"
        gpipath = working_path / "GPI"
        create_directory(gpipath)
        if inputdir == "osm_filtered":
            osm_filtered_path = working_path / inputdir
            gpsbabel_command = f"""
            gpsbabel \\
                -i osm \\
                -f {osm_filtered_path}/filtered_{poi}.osm \\
                -o garmin_gpi,category={poi},bitmap={iconpath}/{poi}.bmp,unique=0\\
                -F {gpipath}/{poi}.gpi"""

        else:
            osm_raw_path = working_path / inputdir
            gpsbabel_command = f"""
            gpsbabel \\
                -i osm \\
                -f {osm_raw_path}/{poi}.osm\\
                -o garmin_gpi,category={poi},bitmap={iconpath}/{poi}.bmp,unique=0\\
                -F {gpipath}/{poi}.gpi"""
        exit_status = run_subprocess(gpsbabel_command)
        if exit_status == 0:
            print(f"Created {gpipath}/{poi}.gpi\n")
    except FileNotFoundError:
        print(f"Error: File not found when trying to create GPI file for POI: {poi}")
    except PermissionError:
        print(f"Error: Permission denied when trying to create GPI file for POI: {poi}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def process_poi(poi, pbf_file_name, poi_dict, working_path, filtering):
    try:
        extract_nodes(pbf_file_name, poi, poi_dict, working_path)
        if filtering:  # If filtering is activated
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
            create_gpi(working_path, "osm_raw", poi)
    except Exception as e:
        print(f"An error occurred while processing POI '{poi}': {str(e)}")


############ MULTIPROCESSING ############


def main_multi(pbf_file_name, filtering):
    start_time = time.time()
    working_path = Path(__file__).parent
    print(f"\n\033[1m\033[34mProcessing {pbf_file_name}...\033[0m")
    print(f"\n\033[1mUsing multiprocessing...\033[0m")
    # Get the number of cores in the CPU
    num_cores = multiprocessing.cpu_count()
    # Use two less than the number of cores
    num_processes = max(1, num_cores - 2)
    print(
        f"Starting multiprocessing. Using {num_processes} of {multiprocessing.cpu_count()} cores"
    )
    if filtering:  # If filtering is activated Green
        print(f"\nFiltering is set to \033[1m\033[32m{filtering}\033[0m\n")
    else:  # If filtering is deactivated Red
        print(f"\nFiltering is set to \033[1m\033[31m{filtering}\033[0m\n")

    try:
        with open("POIs.yaml", "r") as poi_file:
            poi_dict = yaml.safe_load(poi_file)
    except FileNotFoundError:
        print("POIs.yaml file not found.")
        return

    with Pool(num_processes) as p:
        p.starmap(
            process_poi,
            [
                (poi, pbf_file_name, poi_dict, working_path, filtering)
                for poi in poi_dict
            ],
        )
    end_time = time.time()

    # Print the total time
    total_time = end_time - start_time
    print(f"Total time: {total_time} seconds")


############# NORMAL PROCESSING #############


def main_single(pbf_file_name, filtering):
    start_time = time.time()
    working_path = Path(__file__).parent
    print(f"\n\033[1m\033[34mProcessing {pbf_file_name}...\033[0m")
    print(f"\n\033[1mUsing single processing...\033[0m")
    if filtering:  # If filtering is activated Green
        print(f"\nFiltering is set to \033[1m\033[32m{filtering}\033[0m\n")
    else:  # If filtering is deactivated Red
        print(f"\nFiltering is set to \033[1m\033[31m{filtering}\033[0m\n")

    try:
        with open("POIs.yaml", "r") as poi_file:
            poi_dict = yaml.safe_load(poi_file)
    except FileNotFoundError:
        print("POIs.yaml file not found.")
        return

    for poi in poi_dict:
        try:
            extract_nodes(pbf_file_name, poi, poi_dict, working_path)
            if filtering:  # If filtering is activated
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
                create_gpi(working_path, "osm_raw", poi)
        except Exception as e:
            print(f"An error occurred while processing POI '{poi}': {str(e)}")
    end_time = time.time()

    # Print the total time
    total_time = end_time - start_time
    print(f"\nTotal time: {total_time:.2f} seconds")


if __name__ == "__main__":
    if args.m:
        main_multi(args.pbf, args.f)
    else:
        main_single(args.pbf, args.f)
