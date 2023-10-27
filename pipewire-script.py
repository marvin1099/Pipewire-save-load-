#!/bin/python
import subprocess
import argparse
import re
import sys

def get_pipewire_types():
    command_output = subprocess.check_output(["pw-cli", "ls"]).decode("utf-8")
    lines = command_output.splitlines()
    pipewire_types = []
    current_type = {}

    for line in lines:
        line = line.strip()
        if line.startswith("id"):
            if current_type:
                pipewire_types.append(current_type)
            current_type = {}
            match = re.match(r'id (\d+), type (\S+)', line)
            if match:
                current_type['id'] = match.group(1)
                current_type['type'] = match.group(2)
        elif line:
            key, value = line.split(" = ")
            current_type[key.strip()] = value.strip().strip('"')

    if current_type:
        pipewire_types.append(current_type)
    return pipewire_types

def get_sorted_pipewire_types(pipewire_types):
    sorted_types = {
        'Link': [],
        'Node': [],
        'Port': []
    }

    for item in pipewire_types:
        if item['type'].endswith('Link/3'):
            sorted_types['Link'].append(item)
        elif item['type'].endswith('Node/3'):
            sorted_types['Node'].append(item)
        elif item['type'].endswith('Port/3'):
            sorted_types['Port'].append(item)

    return sorted_types['Link'], sorted_types['Node'], sorted_types['Port']

def save_wires(links, nodes, ports, output_file):
    connections = []
    for link in links:
        # Extract relevant information from the link dictionary
        output_port_id = link.get("link.output.port")
        input_port_id = link.get("link.input.port")
        output_node_id = link.get("link.output.node")
        input_node_id = link.get("link.input.node")


        # Match the IDs to names using nodes and ports dictionaries
        outnode_name = next((node["node.name"] for node in nodes if node["id"] == output_node_id), "Unknown")
        innode_name = next((node["node.name"] for node in nodes if node["id"] == input_node_id), "Unknown")
        outnode_class = next((node["media.class"] for node in nodes if node["id"] == output_node_id), "Unknown").replace("/","-")
        innode_class = next((node["media.class"] for node in nodes if node["id"] == input_node_id), "Unknown").replace("/","-")
        outport_name = next((port["port.name"] for port in ports if port["id"] == output_port_id), "Unknown")
        inport_name = next((port["port.name"] for port in ports if port["id"] == input_port_id), "Unknown")

        # Count occurrences for output node
        outnode_occurrence = 0
        for node in nodes:
            if node["id"] == output_node_id:
                break
            if node["node.name"] == outnode_name and node["media.class"] == outnode_class:
                outnode_occurrence += 1

        # Count occurrences for input node
        innode_occurrence = 0
        for node in nodes:
            if node["id"] == input_node_id:
                break
            if node["node.name"] == innode_name and node["media.class"] == innode_class:
                innode_occurrence += 1

        # Store the connection in the connections list
        connection = {
            "outnode_name": outnode_name,
            "outnode_class": outnode_class,
            "innode_name": innode_name,
            "innode_class": innode_class,
            "outport_name": outport_name,
            "inport_name": inport_name,
            "outnode_occurrence": outnode_occurrence,
            "innode_occurrence": innode_occurrence
        }
        connections.append(connection)

    # Print or save the connections list
    with open(output_file, "w") as f:
        for connection in connections:
            f.write(f"outnode_name = {connection['outnode_name']}\n")
            f.write(f"outnode_class = {connection['outnode_class']}\n")
            f.write(f"innode_name = {connection['innode_name']}\n")
            f.write(f"innode_class = {connection['innode_class']}\n")
            f.write(f"outport_name = {connection['outport_name']}\n")
            f.write(f"inport_name = {connection['inport_name']}\n")
            f.write(f"outnode_occurrence = {connection['outnode_occurrence']}\n")
            f.write(f"innode_occurrence = {connection['innode_occurrence']}\n\n")
    print(f"Connections saved to {output_file}\n")

def load_wires(links, nodes, ports, input_file):
    connections = []

    # Open the input file and read the content
    with open(input_file, "r") as f:
        content = f.read()

    # Split the content based on double newlines
    connection_data = content.strip('\n').split("\n\n")

    # Process each connection entry
    for entry in connection_data:
        # Split the entry into lines
        lines = entry.strip().split('\n')

        # Initialize variables for connection information
        connection_info = {
            "outnode_name": None,
            "outnode_class": None,
            "innode_name": None,
            "innode_class": None,
            "outport_name": None,
            "inport_name": None,
            "outnode_occurrence": 0,
            "innode_occurrence": 0
        }

        # Read key-value pairs and populate connection_info
        for line in lines:
            key, value = line.split("=")
            key = key.strip()
            value = value.strip()
            if key in connection_info:
                connection_info[key] = value
        # Convert occurrences to integers
        connection_info["outnode_occurrence"] = int(connection_info["outnode_occurrence"])
        connection_info["innode_occurrence"] = int(connection_info["innode_occurrence"])

        # Restore class name
        connection_info["outnode_class"] = connection_info["outnode_class"].replace("-","/")
        connection_info["innode_class"] = connection_info["innode_class"].replace("-","/")

        # Match connection names with provided links, nodes, and ports dictionaries
        matched_outnode_id = None
        matched_innode_id = None
        for node in nodes:
            if node["node.name"] == connection_info["outnode_name"] and node["media.class"] == connection_info["outnode_class"] and node["node.name"] != "Unknown":
                if connection_info["outnode_occurrence"] == 0:
                    matched_outnode_id = node["id"]
                    break
                else:
                    connection_info["outnode_occurrence"] -= 1

        for node in nodes:
            if node["node.name"] == connection_info["innode_name"] and node["media.class"] == connection_info["innode_class"] and node["node.name"] != "Unknown":
                if connection_info["innode_occurrence"] == 0:
                    matched_innode_id = node["id"]
                    break
                else:
                    connection_info["innode_occurrence"] -= 1

        # If all IDs are found, add the connection to connections list
        if matched_outnode_id and matched_innode_id:
            outport_id = next((port["id"] for port in ports if port["port.name"] == connection_info["outport_name"] and port["node.id"] == matched_outnode_id), None)
            inport_id = next((port["id"] for port in ports if port["port.name"] == connection_info["inport_name"] and port["node.id"] == matched_innode_id), None)

            if outport_id and inport_id:
                matched_connection = {
                    "link.output.port": outport_id,
                    "link.input.port": inport_id,
                    "link.output.node": matched_outnode_id,
                    "link.input.node": matched_innode_id,
                }
                connections.append(matched_connection)
        else:
            print("Warning: Incomplete or mismatched connection - Skipped")
            for key, value in connection_info.items():
                print(f"{key} = {value}")
            print("Mached was " + str(matched_outnode_id) + " " + str(matched_innode_id))
            print("")


    # Create PipeWire links using pw-link command
    for connection in connections:
        outport = connection["link.output.port"]
        inport = connection["link.input.port"]
        subprocess.run(["pw-link", outport, inport])
    print(f"\nConnections loaded from {input_file}\n")

def get_info_by_key(data_list, search_key, search_value, output_key):
    results = []
    for item in data_list:
        if item.get(search_key) == search_value:
            results.append(item.get(output_key))
    return results

def print_all_keys(data_list):
    all_keys = set()
    for item in data_list:
        all_keys.update(item.keys())
    print("All Keys:")
    for key in all_keys:
        print(key)
    print("\n")

def main():
    parser = argparse.ArgumentParser(description="Manage PipeWire connections.")
    parser.add_argument("-s", "--save", action="store_true", help="Save wires")
    parser.add_argument("-l", "--load", action="store_true", help="Load wires")
    parser.add_argument("-d", "--data", choices=["links", "ports", "nodes"], help="Select data type (links, ports, nodes) for searching")
    parser.add_argument("-k", "--keys", action="store_true", help="Print all keys of data")
    parser.add_argument("-i", "--list", action="store_true", help="List all items of data")
    parser.add_argument("-q", "--query", help="Search key")
    parser.add_argument("-v", "--value", help="Search value")
    parser.add_argument("-o", "--output", help="Output key for the search")
    parser.add_argument("-c", "--config", default="pipewirewires.conf", help="Config file to use (default: pipewirewires.conf)")

    args = parser.parse_args()

    # Display help if no main arguments are provided
    if not any([args.save, args.load, args.data]):
        parser.print_help()
    else:
        pipewire_types = get_pipewire_types()
        links, nodes, ports = get_sorted_pipewire_types(pipewire_types)

        if args.save:
            save_wires(links, nodes, ports, args.config)
        if args.load:
            load_wires(links, nodes, ports, args.config)

        if args.data and args.query and args.value and args.output:
            if args.data == "links":
                results = get_info_by_key(links, args.query, args.value, args.output)
            elif args.data == "nodes":
                results = get_info_by_key(nodes, args.query, args.value, args.output)
            elif args.data == "ports":
                results = get_info_by_key(ports, args.query, args.value, args.output)
            else:
                print("Invalid data type. Use 'links', 'ports', or 'nodes'.")
        if args.data and args.keys:
            if args.data == "links":
                print_all_keys(links)
            elif args.data == "nodes":
                print_all_keys(nodes)
            elif args.data == "ports":
                print_all_keys(ports)
            else:
                print("Invalid data type. Use 'links', 'ports', or 'nodes'.")
            print("Results:\n" + results.join("\n") + "\n\n")
        if args.data and args.list:
            data_list = []
            if args.data == "links":
                data_list = links
            elif args.data == "nodes":
                data_list = nodes
            elif args.data == "ports":
                data_list = ports
            else:
                print("Invalid data type. Use 'links', 'ports', or 'nodes'.")
            if data_list != []:
                for item in data_list:
                    print("")
                    for key, value in item.items():
                        print(f"{key} = {value}")
                print(f"\nIn total there are {len(data_list)} {args.data}\n\n")

if __name__ == "__main__":
    main()
