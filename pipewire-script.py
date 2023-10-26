#!/bin/python
import subprocess
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
        outport_name = next((port["port.name"] for port in ports if port["id"] == output_port_id), "Unknown")
        inport_name = next((port["port.name"] for port in ports if port["id"] == input_port_id), "Unknown")

        # Count occurrence of nodes with the same name before the current node
        outnode_occurrence = len([node for node in nodes if node["node.name"] == outnode_name and node["id"] != output_node_id])
        innode_occurrence = len([node for node in nodes if node["node.name"] == innode_name and node["id"] != input_node_id])

        # Store the connection in the connections list
        connection = {
            "outnode_name": outnode_name,
            "innode_name": innode_name,
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
            f.write(f"innode_name = {connection['innode_name']}\n")
            f.write(f"outport_name = {connection['outport_name']}\n")
            f.write(f"inport_name = {connection['inport_name']}\n")
            f.write(f"outnode_occurrence = {connection['outnode_occurrence']}\n")
            f.write(f"innode_occurrence = {connection['innode_occurrence']}\n\n")
    print(f"Connections saved to {output_file}")

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
            "innode_name": None,
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

        # Match connection names with provided links, nodes, and ports dictionaries
        matched_outnode_id = None
        matched_innode_id = None

        for node in nodes:
            if node["node.name"] == connection_info["outnode_name"] and node["node.name"] != "Unknown":
                if connection_info["outnode_occurrence"] == 0:
                    matched_outnode_id = node["id"]
                    break
                else:
                    connection_info["outnode_occurrence"] -= 1

        for node in nodes:
            if node["node.name"] == connection_info["innode_name"] and node["node.name"] != "Unknown":
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

    # Create PipeWire links using pw-link command
    for connection in connections:
        outport = connection["link.output.port"]
        inport = connection["link.input.port"]
        subprocess.run(["pw-link", outport, inport])

def get_id_from_name(name, obj):
    key = ''
    if any('port.name' in part for part in obj):
        key = 'port.name'
    elif any('node.name' in part for part in obj):
        key = 'node.name'
    else:
        if key != '':
            return []

    obj_ids = [part["id"] for part in obj if part[key] == name]
    return obj_ids

output_file = "pipewirewires.conf"

if len(sys.argv) < 2:
    print("Usage:")
    print("./wipewire-script.py save                             - To save wires")
    print("./wipewire-script.py load                             - To load wires")
    print("./wipewire-script.py getpid 'nodename'                - To get nodeid")
    print("./wipewire-script.py getnid 'portname'                - To get portid")
    print("./wipewire-script.py lsnodes                          - To list all nodes with names")
    print("./wipewire-script.py lsports                          - To list all ports with names")
    print("The config that is used for save and load is ./pipewirewires.conf")
    sys.exit(1)

if __name__ == "__main__":
    pipewire_types = get_pipewire_types()
    links, nodes, ports = get_sorted_pipewire_types(pipewire_types)

if sys.argv[1] == "save":
    save_wires(links, nodes, ports, output_file)

elif sys.argv[1] == "load":
    load_wires(links, nodes, ports, output_file)

elif sys.argv[1] == "getpid":
    if len(sys.argv) < 3:
        print("Error: Port name is required.")
        sys.exit(1)
    port_ids = get_id_from_name(sys.argv[2], ports)
    if port_ids:
        print("\n".join(port_ids))
    else:
        print("Error: No ports not found.")

elif sys.argv[1] == "getnid":
    if len(sys.argv) < 3:
        print("Error: Node name is required.")
        sys.exit(1)
    node_ids = get_id_from_name(sys.argv[2], nodes)
    if node_ids:
        print("\n".join(node_ids))
    else:
        print("Error: No nodes not found.")

elif sys.argv[1] == "lsnodes":
    for i in nodes:
        print("")
        for k, v in i.items():
            print(k + " = " + v)
    print("")
    print("In total there are " + str(len(nodes)) + " nodes")

elif sys.argv[1] == "lsports":
    for i in ports:
        print("")
        for k, v in i.items():
            print(k + " = " + v)
    print("")
    print("In total there are " + str(len(ports)) + " ports")
