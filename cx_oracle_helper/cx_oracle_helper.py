from collections import namedtuple
from importlib.util import find_spec
from sys import exit
from typing import Union, TypeVar
from textwrap import dedent

from cx_oracle_helper.templates import insert_placeholder

import cx_Oracle

if find_spec('cx_oracle_helper.db') is not None:
    try:
        from cx_oracle_helper.db import DATABASES, ORACLE_CLIENT

        if len(ORACLE_CLIENT):
            cx_Oracle.init_oracle_client(lib_dir=ORACLE_CLIENT)

    except ModuleNotFoundError or ImportError:
        raise ModuleNotFoundError("db module not found")
    except cx_Oracle.ProgrammingError as e:
        print(e)
        exit(1)


class CxohDatabaseNotFound(KeyError):
    pass


class CxohConnectionError(KeyError):
    pass

class CxohDatabaseError(cx_Oracle.DatabaseError):
    pass

class CxohMissingArgument(TypeError):
    pass

class CxohInterfaceError(cx_Oracle.InterfaceError):
    pass

TCxOracleHelper = TypeVar("TCxOracleHelper", bound="CxOracleHelper")

class CxohResultSet:
    def __init__(self, data):
        self.__data = data
        self.__validate_data_keys()

        self.columns = data["columns"]  
        self.rows = data["rows"]

    def __len__(self):
        return len(self.rows)

    def __repr__(self) -> str:
        return f"<{CxohResultSet.__name__}({self.columns}, rows[{len(self.rows)}])>"

    def __validate_data_keys(self):
        if "columns" not in  self.__data or not "rows" in self.__data:
            raise Exception("Invalid data structure: rows or columns are missing.")
    
    @property
    def as_namedtuple(self):
        DataTable = namedtuple(CxohResultSet.__name__, self.columns)
        return list(map(DataTable._make, self.rows))

class CxOracleHelper:
    
    def __init__(self, db_name: str, call_timeout=Union[None, int]):
        self.__db_name = db_name
        self.__conn = self.__make_db_connection()
        
        if call_timeout is not None and isinstance(call_timeout, int):
            self.__conn.call_timeout = call_timeout
    
    def __repr__(self) -> str:
        return f"<{CxOracleHelper.__name__}('{self.__db_name}')>"

    @property
    def __db_obj(self):
        self.__validate_db_name()
        db_access_obj = DATABASES[self.__db_name]
        return db_access_obj

    def __make_db_connection(self):
        if not self.__db_obj.get("sid", False) and not self.__db_obj.get("service_name", False):
            raise CxohConnectionError(f'SID or Service Name must be specified in {self.__db_name} object.')

        if self.__db_obj.get("sid", False):
            dsn = cx_Oracle.makedsn(self.__db_obj["host"], self.__db_obj["port"], sid=self.__db_obj["sid"])
        else:
            dsn = cx_Oracle.makedsn(self.__db_obj["host"], self.__db_obj["port"], service_name=self.__db_obj["service_name"])

        connection = cx_Oracle.connect(**self.__db_obj["credentials"], dsn=dsn, encoding="UTF-8")

        return connection

    def __validate_db_name(self):
        if not DATABASES.get(self.__db_name, False):
            databases = list(DATABASES.keys())
            raise CxohDatabaseNotFound(
                f"DB Name \"{self.__db_name}\" not found: {databases}"
            )

    def __validate_execute_args(self, args):
        if not args['fetch'] in ["all"] and not isinstance(args['fetch'], int):
            raise CxohMissingArgument(f"Invalid fetch{['all', int]} argument value: -> {args['fetch']} {type(args['fetch'])}")

        if isinstance(args["data"], list) and not bool(len(args["data"])):
            raise CxohMissingArgument(f"Data is missing to executemany: -> {args['data']}")

        if args["many"]:
            if args["data"] is None:
                raise CxohMissingArgument(f"executemany cannot be called without data.")
        else:
            if isinstance(args["data"], list) and len(args["data"]) > 0:
                raise CxohMissingArgument(f"Data must be set with executemany: many -> {args['many']}")

    def __validate_execute_data_transfer_args(self, args):  
            if args["target"] is not None and not args["target"].get("dest_table", False) and not args["target"].get("connection", False):
                raise CxohMissingArgument(f"dest_table and connection keys must be specified in target -> {args['target']}")

    def __print_batch_errors(errors):
        for error in errors:
            print(f"Error {error.message} at row offset {error.offset}")

    def __fetch(self, cursor, value: Union[str, int]):
        table_data = { "columns": self.__table_columns(cursor.description) }

        if isinstance(value, int):
            return CxohResultSet({ "rows": cursor.fetchmany(value), **table_data })

        f_data = {
            'all': CxohResultSet({ "rows": cursor.fetchall(), **table_data })
        }

        return f_data[value]
    
    def __table_columns(self, cursor_description: any):
        return [column[0] for column in cursor_description]   

    def get_table_columns(self, table_name):
        data, _, error = self.execute(f"select COLUMN_NAME from ALL_TAB_COLUMNS where TABLE_NAME='{table_name.upper()}'")
        if error is not None:
            return error
        return [row.COLUMN_NAME for row in data.as_namedtuple]

    def execute(self, 
        sql_or_proc: str,
        fetch: Union[str, int]='all',
        commit=False,
        many=False,
        data: Union[None, list]=None,
        exec_proc=False,
        proc_params=[]
    ):
        """
        :param sql_or_proc: SQL or Procedure statement.
        :param fetch: The number of rows to be fetched.
        :param commit: Apply commit to dml statements that requires it,
        :param many: Used for executemany function. It should be used with data parameter
        :param data: Dataset to be used by a dml operation. It should be used with many parameter
            e.g conn.execute(sql, many=True, data=[..])
        :param exec_proc: Take the sql parameter value as a pl/sql.
        :param proc_params: Array of parameters for a procedure.
            e.g conn.execute(procedure, exec_proc, proc_params=[...])
        """
        self.__validate_execute_args(locals())

        result = None
        error = None
        commited = False
        
        try:
            with self.__conn.cursor() as cursor:
                
                if exec_proc:
                    exec_data = cursor.callproc(sql_or_proc, proc_params)
                else:
                    if not many:
                        exec_data = cursor.execute(sql_or_proc)
                        
                        if commit:
                            self.__conn.commit()
                            commited = True
                        else:
                            result = self.__fetch(cursor, fetch) if exec_data is not None else None
                    else:
                        cursor.executemany(sql_or_proc, data, batcherrors=True)
                        errors = cursor.getbatcherrors()

                        if bool(len(errors)):
                            errors = cursor.getbatcherrors()
                            self.__print_batch_errors(errors)
                            error = errors
                        else:
                            self.__conn.commit()
                            commited = True

        except CxohDatabaseError as error:
            self.__conn.close()
            error = error
        finally:
            return result, commited, error

    def execute_data_transfer(self, origin_sql: str, target: dict, num_rows: int = 100):
        """Transfer data from a database table to another that use the same schema structure
        TODO: This should be reusable for different cases. A Proof of concept yet.
        """
        self.__validate_execute_data_transfer_args(locals())
        input(dedent("""\
            - To transfer data from a database to another, make sure the structure of both tables are the same...
            [ENTER] to Continue, [Ctrl + C] to Cancel\n\n
        """)) 
        try:
            # target
            target_conn = target["connection"]
            target_table = target["dest_table"]

            with self.__conn.cursor() as cursor:
                cursor.execute(origin_sql)
                sql_insert = insert_placeholder(target_table, self.__table_columns(cursor.description))
                rows_inserted = 0

                while True:
                    rows = cursor.fetchmany(num_rows)
                    if not rows:
                        break

                    target_conn.execute(sql_insert, many=True, data=rows)

                    rows_inserted += len(rows)

                return {"status": f"{rows_inserted} Rows inserted."}
        except CxohDatabaseError as error:
            self.__conn.close()
            return {"error": f"[ERROR]: {str(error)}"}
