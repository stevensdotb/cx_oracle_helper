import csv
from functools import wraps, partial
from time import time

def runtime(func=None, logger=None):
    """Show the time execution. The decorator should be at the top in case of using multiple decorators
    Example:
        @runtime
        @decorator
        @another_decorator
        def function(): ...
    """
    if func is None:
        return partial(runtime, logger=logger)

    def wrapper(*args, **kwargs):
        start = time()
        data = func(*args, **kwargs)
        end = time()
        timed_str = f"Time execution: {end - start:.3}"

        if logger is not None:
            logger.info(timed_str)
        else:
            print(timed_str)

        return data
    return wrapper


def dict_based(data_function):
    """Return the data as a list of dictionries"""
    def wrapper():
        data = data_function()
        if data is not None:
            return [
                {
                    column_name:field 
                    for (column_name, field) in zip(data.columns, row)
                } for row in data.rows
            ]
    return wrapper

def csv_export(func=None, file: str = None, logger=None):
    """Import the data retrieve from a queryset in a CSV File
    :param: func -> Wrapped function
    :param: file -> file where the data will be imported. Absolute or relative path
    """
    if func is None:
        return partial(csv_export, file=file)

    if file is None:
        raise Exception("File needs to be specified to export the data")

    @wraps(func)
    def wrapper(*args, **kwargs):
        *_, file_ext = tuple(file.split('.'))
        data = func(*args, **kwargs)

        if data is not None and file_ext == "csv":
            with open(file, "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=';')
                csv_writer.writerow(data.columns)
                csv_writer.writerows(data.rows)
                if logger is not None:
                    logger.info(f"Data exported to {file}")
                else:
                    print(f"Data exported to {file}")
        return data

    return wrapper