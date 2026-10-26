import glob
import os
from pathlib import Path

import yaml


def load_parameters(module_dir_name):
    """
    Responsible for reading the package parameter values from the included yaml file.
    """
    module_dir_name = module_dir_name.lower()
    try:
        this_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        data_dir = this_dir.parent.parent / "data"

        with open(
            os.path.join(data_dir, module_dir_name, "cq_parameters.yaml"), "r"
        ) as f:
            all_params = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

    return all_params


def load_aux_parameters(file, yaml_name):
    """
    Sometimes there are auxiliary global parameters that need to be loaded from file,
    and this method does that.
    """

    try:
        this_dir = os.path.dirname(os.path.abspath(file))

        with open(os.path.join(this_dir, yaml_name), "r") as f:
            all_params = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

    return all_params


def load_data_parameters(data_module_dir_name):
    """
    Responsible for reading the package parameter values from merging data/<module_name>/*.yaml files.
    """
    all_params = {}
    try:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        allFiles = glob.glob(f"{this_dir}/../../data/{data_module_dir_name}/*.yaml")
        for file in allFiles:
            with open(file) as f:
                params = yaml.load(f, Loader=yaml.FullLoader)
                if not params:
                    continue
                for key in params:
                    all_params[key] = params[key]
    except yaml.YAMLError as exc:
        print(exc)

    return all_params
