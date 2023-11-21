import pandas as pd
import numpy as np
from typing import List
import time, os, h5py

def create_path_filename(measurement_name: str, path: str = None):
    """Creates a filename with date and timestamp.

    Args:
        measurement_name (str): Measurement name. A string to identify the type of measurement done.
        path (str, optional): Path that contains the data folder. A subfolder will be created here with 20xx-xx-xx subfolder structure. Defaults to None.

    Returns:
        _type_: Path with h5 extension.
    """
    path = 'data/' if path is None else path
    subdir = os.path.join(path, time.strftime("%Y-%m-%d"))
    try:
        os.mkdir(subdir)
    except Exception:
        pass
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = timestr + "_" + measurement_name + ".h5"
    filepath = os.path.join(subdir, filename)
    return filepath

def save_nd_sweep(filepath: str, data_array : np.ndarray, index_arrays: list, data_column_names: list, index_names: list, 
                  h5_key: str = "ndsweep"):
    """Save a multi-dimensional sweep where all data is already available. For saving the data piecewise as it is being recorded, see `append_2d_sweep`
    This function is suitable if each quantity has a single value at each sweep point, e.g. the magnitude at a single frequency vs. two voltage values.
    
    Some things to remember: 
    - data_array is a list of data. data_array.shape = n x m
    - data_column_names is a list of strings. len(data_column_names) = m
    - index_arrays is a list of several arrays: [index_a, index_b, ...]. These arrays may be different lengths.
    len(index_a) * len(index_b) * ... = n. The order of index_a and index_b is important.
    - index_names is a list of strings. len(index_names) = len(index_arrays)

    Args:
        filepath (str): Filepath with h5 extension.
        data_array (np.ndarray): Data array with dimensions n x m
        index_arrays (list): List of index arrays, or floats if a voltage is constant. These are the sweep axes values.
        data_column_names (list): The names of the quantities being recorded, e.g. magnitude and phase of a signal
        index_names (list): Names of the sweep axes (e.g. which voltages are swept)
        h5_key (str, optional): h5 key. Defaults to "ndsweep".

    Returns:
        _type_: None
    """
    # Checks for consistency:
    n, m = np.shape(data_array)
    
    assert len(data_column_names) == m
    assert len(index_names) == len(index_arrays)
    
    df = pd.DataFrame(data_array, 
                      index=pd.MultiIndex.from_product(index_arrays, names=index_names), 
                      columns=data_column_names)
    
    keys = get_keys(filepath)
    
    if h5_key in keys:
        print("h5_key already exists, data not saved!")
    else:
        df.to_hdf(filepath, key=h5_key, mode='a')
    
    return None

def append_nd_sweep(filepath: str, data_array : np.ndarray, index_arrays: list, data_column_names: list, index_names: list, 
                    h5_key: str = "2dsweep"):
    """Build a multi-dimensional pandas dataframe as data comes in. This method can be used for 1d, 2d and arbitrary dimensional sweeps.

    Args:
        filepath (str): Filepath with h5 extension.
        data_array (np.ndarray): Data array with dimensions n x m, where n, m >= 1
        index_arrays (list): List of index arrays, or floats if a voltage is constant. These are the sweep axes values.
        data_column_names (list): The names of the quantities being recorded, e.g. magnitude and phase of a signal
        index_names (list): Names of the sweep axes (e.g. which voltages are swept)
        h5_key (str, optional): h5 key. Defaults to "2dsweep".

    Returns:
        _type_: None
    """
    
    keys = get_keys(filepath)
    existing_df = open_file(filepath, h5_key)
    
    df = pd.DataFrame(data_array, 
                        index=pd.MultiIndex.from_product(index_arrays, names=index_names), 
                        columns=data_column_names)

    if h5_key in keys:
        # The key already exists, we can append to it
        new_df = pd.concat([existing_df, df])
        new_df.sort_index()
        new_df.to_hdf(filepath, key=h5_key, mode='a')
        
    else:
        # This is the first time we access the key, no need to append.
        df.to_hdf(filepath, key=h5_key, mode='a')
    
    return None
    
def save_dict(filepath: str, data_dict : dict, h5_key: str="dictionary", mode: str='append'):
    """Saves a dictionary to an h5 file. If mode = 'append' this function points to append_dict

    Args:
        filepath (str): Filepath with h5 extension.
        data_dict (dict): Dictionary to be saved
        h5_key (str, optional): h5 key. Defaults to "dictionary".
        mode (str, optional): If mode = 'append' this function points to append_dict. Defaults to 'append'.
    """
    df = pd.DataFrame([data_dict])
    keys = get_keys(filepath)
        
    if h5_key in keys:
        if mode == 'append':
            append_dict(filepath, data_dict, h5_key=h5_key)
        else:
            print("h5_key already exists, data not saved!")
    else:
        df.to_hdf(filepath, key=h5_key, mode='a')
    


def append_dict(filepath: str, data_dict : dict, h5_key: str="dictionary"):
    """Append a dictionary to an existing h5_key in an h5 file located in filepath.

    Args:
        filepath (str): Filepath with h5 extension.
        data_dict (dict): Dictionary with keys that match the existing keys.
        h5_key (str, optional): key name of the existing h5_key. Defaults to "dictionary".
    """
    
    df = open_file(filepath=filepath, h5_key=h5_key)
    df2 = pd.DataFrame([data_dict])
    
    new_df = pd.concat([df, df2], ignore_index=True)
    new_df.to_hdf(filepath, key=h5_key, mode='a')
    
def open_file(filepath: str, h5_key: str = "2dsweep"):
    """Opens a file and returns the pandas DataFrame object

    Args:
        filepath (str): Filepath with h5 extension.
        h5_key (str, optional): h5 key. Defaults to "2dsweep".

    Returns:
        Dataframe Object: Pandas DataFrame object
    """
    if h5_key in get_keys(filepath):
        return pd.read_hdf(filepath, key=h5_key)
    else:
        print(f"h5_key {h5_key} does not exist! These are all available h5_keys:")
        print(get_keys(filepath))

def get_keys(filepath: str):
    """Lists the keys in an h5 file. Handy for checking if a key exists.

    Args:
        filepath (str): Filepath with h5 extension.

    Returns:
        List: list of keys.
    """
    if os.path.exists(filepath):
        # Read if the chosen key already exists:
        with h5py.File(filepath, "r") as f:
            keys = list(f.keys())
    else:
        keys = []
    
    return keys