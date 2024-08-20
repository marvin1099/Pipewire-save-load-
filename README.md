# PipewireSaveLoad

Python script to save and load your pipewire wires.  
Also a search function is included since its nice to have.  
Also keep in mind the current version is only compatible with configs created at 0.3.2 or higher.  
I want to say I used AI a lot for to make this script,   
this is just one of these set it and forget it scripts.

## Download
Go To:  
Main Repo: https://codeberg.org/marvin1099/Pipewire-save-load/releases  
Backup Repo: https://github.com/marvin1099/Pipewire-save-load/releases  
Then download the pipewire-script.py file and run it with the desired options   

## Extra Info
Keep in mind the script replaces / to - in innode_class and outnode_class  
It also replaces : to - in innode_name and outnode_name  
It is doing this to make the config look nice,  
so if you dont want it remove it in the save and load function.  

## Usage

    usage: pipewire-script.py [-h] [-s] [-l] [-d {links,ports,nodes}] [-k] [-i] 
                              [-q QUERY] [-v VALUE] [-o OUTPUT] [-c CONFIG]

    Manage PipeWire connections.

    options:
    -h, --help            show this help message and exit
    -s, --save            Save wires
    -l, --load            Load wires
    -d {links,ports,nodes}, --data {links,ports,nodes}
                          Select data type (links, ports, nodes) for searching and listing
    -k, --keys            Print all keys of data
    -i, --list            List all items of data
    -q QUERY, --query QUERY
                          Search key
    -v VALUE, --value VALUE
                          Search value
    -o OUTPUT, --output OUTPUT
                          Output key for the search
    -c CONFIG, --config CONFIG
                          Config file to use (default: pipewirewires.conf)