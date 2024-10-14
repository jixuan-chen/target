import re
import os
import tqdm
import json
import math
import numpy as np
import pandas as pd
from configparser import ConfigParser


def read_config(config_file_path):
    if not os.path.exists(config_file_path):
        raise ValueError("The config file '{}' could not be found.".format(config_file_path))

    config = ConfigParser()
    config.read(config_file_path)
    return config.defaults()


def parse_formula(dct, value):
    if isinstance(value, str):
        if value.startswith("formula_"):
            form = value.replace("formula_", "")
            paras = re.findall("\$+\w*", value)

            for par in paras:
                subs = par.replace("$", "dct['").replace("_", "']['") + "']"
                form = form.replace(par, subs)

            return eval(form)
        else:
            raise ValueError("The parameters json file you provided has an invalid entry: '{}'".format(
                value))
    else:
        return value


def parse_json(dct):
    parsed_one = {}
    for key, val in dct.items():
        parsed_one[key] = val["value"]

    parsed_two = {}
    for key, val in parsed_one.items():
        if isinstance(val, dict):
            dct2 = {}
            for key2, val2 in val.items():
                dct2[key2] = parse_formula(parsed_one, val2)
            parsed_two[key] = dct2
        elif isinstance(val, list):
            lst = []
            for v in val:
                lst.append(parse_formula(parsed_one, v))
            parsed_two[key] = lst
        else:
            parsed_two[key] = parse_formula(parsed_one, val)
    return parsed_two


def load_json(file_path):
    with open(file_path, "r") as jsn:
        parameters = json.load(jsn)
    return parse_json(parameters)

def npy_to_csv(file, progress=False):
    """
    This function converts a .npy file to many corresponding csv files.

    :param file: str, file path to binary numpy results file (.npy)
    :param progress: bool, decides if progress bar is shown
    """

    folder, name = os.path.split(file)
    file_name, _ = os.path.splitext(name)

    csv_folder = os.path.join(folder, "csv")
    if not os.path.exists(csv_folder):
        os.mkdir(csv_folder)

    array = np.load(file, allow_pickle=True)

    columns = array[0].dtype.names
    for time_step in tqdm.tqdm(range(array.shape[0]), disable=progress):
        datestr = array[time_step]["date"][0][0].strftime("%F %H_%M_%S")
        df = pd.DataFrame()
        for c in columns[:-1]:
            df[c] = array[time_step][c].flatten()

        df.to_csv(
            os.path.join(
                csv_folder,
                file_name + "_" + datestr + ".csv"
            ),
            sep=";",
            index=False
        )

