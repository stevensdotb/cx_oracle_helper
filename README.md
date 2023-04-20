# Cx Oracle Helper

Package to perform simple operations over Oracle easily with [cx_Oracle](https://cx-oracle.readthedocs.io/en/latest/ "https://cx-oracle.readthedocs.io/en/latest/") and Python.

### Install

* Clone the repo into your project folder
* `cd cx_oracle_helper`
* `pip install .`
* Start using the package into your script
  `from cx_oracle_helper import CxOracleHelper`

### DB Config File

Generate a `dbconfig.join` file to store all database information and if needed the Oracle Client plugin path and add it to the package itself to be read.

```bash
# Generate a dbconfig.json
python -m cx_oracle_helper --gdbf
# Once you modified the dbconfig.json file then
python -m cx_oracle_helper --add-config-file=dbconfig.json
# The db.py module will be created into the package itself to be read
```

If the file is not created and add it to the package, the following error will be thrown:
`ModuleNotFoundError: db.py module not found.` or `NameError: DATABASES is not defined.`

Structure:

- `ORACLE_CLIENT`:  Store the path of the [oracle instant client](https://www.oracle.com/database/technologies/instant-client/downloads.html) plugin required for cx_Oracle.
- `DATABASES`: Stores the Databases credentials for each environment.

See [sample.ipynb](./sample.ipynb)
