import argparse
import json
from os import path, getcwd
from platform import system
from sys import exit


databases_tpl = {
    "DB_NAME": {
        "host": "",
        "port": None,
        "sid": "",
        "credentials": {
            "user": "",
            "password": ""
        }
    },
    "DB_NAME_2": {
        "host": "",
        "port": None,
        "service_name": "",
        "credentials": {
            "user": "",
            "password": ""
        }
    }
}

# Template
db_config_tpl = {
    "ORACLE_CLIENT_PATH": "",
    "DATABASES": databases_tpl
}


parser = argparse.ArgumentParser(description='Generate a config file to set the database access.')
parser.add_argument('--gdbf', type=bool, action=argparse.BooleanOptionalAction, help='Generate dbconfig.json file.')
parser.add_argument('--add-config-file', type=str, help="Path of the config file. It will add the config file to the package it self to be read.")
args = parser.parse_args()

def generate_file():
    dbconfig_file = "dbconfig.json"
    dbconfig_path = path.join(getcwd(), dbconfig_file)

    if path.exists(dbconfig_path):
        print(f"~ {dbconfig_file} already exists in this directory. Remove it or rename the file.")
        exit(1)

    with open(dbconfig_path, "w") as file:
        json.dump(db_config_tpl, file, indent=4)
        print(f"~ {dbconfig_file} generated in {getcwd()}")

def add_config():
    with open(path.abspath(args.add_config_file), "r") as json_file:
        config = json.load(json_file)
    
    db_file_path = path.join(path.dirname(path.abspath(__file__)), "db.py")
        
    with open(db_file_path, "w") as db_file:
        oracle_client = config.get('ORACLE_CLIENT_PATH', False)
        db_access = config.get('DATABASES', False)

        if not oracle_client:
            oracle_client = ""
        else:
            oracle_client = oracle_client.replace("/", "\\\\") if system() == 'Windows' else oracle_client

        db_file.write(f"ORACLE_CLIENT = '{oracle_client}'\n")

        if not db_access or not len(db_access):
            raise KeyError("DATABASES structure is needed. If you lost the structure, run --gbdf to generate the dbconfig.json again.")
        
        db_file.write(f"DATABASES = {db_access if db_access else dict()}")
    
    print("~ Config file applied as module in:")
    print(f" {db_file_path}")

def config_manager():
    if args.gdbf:
        generate_file()

    if args.add_config_file:
        add_config()
    
    exit(1)

