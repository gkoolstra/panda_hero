import pandas as pd
import numpy as np
from typing import List
import time, os, h5py
import glob
import yaml

def create_path_filename(measurement_name: str, path: str = None, chip_info_path: str = None):
    """Creates a filename with date and timestamp. Saves device information to file if information is included.

    Args:
        measurement_name (str): Measurement name. A string to identify the type of measurement done.
        path (str, optional): Path that contains the data folder. A subfolder will be created here with 20xx-xx-xx subfolder structure. Defaults to None.
        chip_info_path (str, optional): Path that contains the device information in a yaml file. Saves dictionary in yaml to path as pandas dataframe and adds chip ID to filename. Defaults to None.  
    Returns:
        _type_: Path with h5 extension.
    """
    path = 'data/' if path is None else path
    
    if chip_info_path:
        with open(chip_info_path, 'r') as f:
            chip_info_dict = yaml.safe_load(f)
        setup_name = chip_info_dict['setup'].lower()
    else:
        setup_name = ""

    subdir = os.path.join(path, time.strftime("%Y-%m-%d"), setup_name)
    try:
        os.mkdir(subdir)
    except Exception:
        pass
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S")
    if chip_info_path:
        chip_name = chip_info_dict['id']
        filename = timestr + "_" + chip_name + "_" + measurement_name + ".h5"
        filepath = os.path.join(subdir, filename)   
        save_dict(filepath, chip_info_dict, 'chip_info')
    else:
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
        
    # Prevent exponential filesize growth 
    temp_filepath = filepath[:-4]+"_temp.h5"
    os.rename(filepath, temp_filepath)
    keys = get_keys(temp_filepath)
    for key in keys:
        existing_df = open_file(temp_filepath, key)
        existing_df.to_hdf(filepath, key=key, mode='a')
    
    os.remove(temp_filepath)
    
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

###NOTE: THE METHODS DEFINED BELOW ARE ALL USED FOR DATA CHUNKING STORAGE. SIGNIFICANT SLOWDOWN OCCURS WHEN LARGE DATASETS ARE SAVED TO A NETWORK DRIVE.
# "CHUNKING" DATASETS INTO SMALLER FILES, STORING THEM LOCALLY, AND COMBINING THEM INTO A SINGLE H5 ONCE A SCAN IS COMPLETE IS FASTER. 

def get_working_temp_file(temp_local_dir: str, chip_info_path: str=None) -> str:
    """Called when chunking a file. Opens a file and returns the pandas DataFrame object. 

    Args:
        temp_local_dir (str): Local directory where data is saved.
        chip_info_path (str, optional): Path that contains the device information in a yaml file. Saves dictionary in yaml to filepath in temp_local_dir as pandas dataframe. Defaults to None.  
    Returns:
        filepath (str): Updated filepath if input path is too big"""
    
    if os.listdir(temp_local_dir) == []:
        print("empty directory!")
        time_str = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = str("0000_"+time_str +'_temp'+ ".h5")
        filepath = os.path.join(temp_local_dir, filename)
    else:
        filename = sorted(os.listdir(temp_local_dir))[-1]
        filepath = os.path.join(temp_local_dir, filename)

    if chip_info_path:
        with open(chip_info_path, 'r') as f:
            chip_info_dict = yaml.safe_load(f)
            chip_name = chip_info_dict['id'] 
            save_dict(filepath, chip_info_dict, 'chip_info')
    else:
        pass
    return filepath


def check_filesize(filepath: str, max_filesize: int) -> str:
    """Takes in a filepath, checks its size and returns either the same filepath, or generates a new filepath 
    if the input path is too large.

    Args:
        filepath (str): Filepath with h5 extension.
        filesize (int): max size of files that are temporarily saved

    Returns:
        filepath (str): Updated filepath used to store data"""
    
    file_size = os.stat(filepath).st_size
    if file_size<=max_filesize:
        return filepath
    elif file_size>max_filesize:
        print("bigger than max size")
        index_prev_str = filepath.split("\\")[-1].split("_")[0]
        index_prev = int(index_prev_str)
        index_curr = index_prev+1
        index_curr_str = "{:04d}".format(index_curr)
        new_filepath = filepath.replace(index_prev_str, index_curr_str)
        return new_filepath
    else:
        pass


def create_temp_dir(measurement_name: str , local_dir:str , chip_info_path: str=None) -> str:
    """Creates a local directory for saving data
    Args:
        measurement_name (str): what you want to call the experiment, eg: 'unloading_sweep' 
        local_dir (str) : path where data will be stored locally
        chip_info_path (str, optional): Path to yaml file with device information. Defaults to None.
    Returns:
        filepath (str) : Directory with measurement_name and date/time in path name"""
    time_str = time.strftime("%Y-%m-%d_%H-%M-%S")
    if chip_info_path:
        with open(chip_info_path, 'r') as f:
            chip_info_dict = yaml.safe_load(f)
        chip_name = chip_info_dict['id']
        temp_local_dir = os.path.join(local_dir, time_str + "_" + chip_name + "_" + measurement_name)
    else:
        temp_local_dir = os.path.join(local_dir, time_str+"_"+measurement_name)
    os.mkdir(temp_local_dir)
    return temp_local_dir


def get_unique_keys(temp_local_dir: str) -> list:
    """Used once multiple datasets from same scan are saved. 
    Looks through all the keys of those data sets, and extracts a list of all unique keys in those files
    
    Args:
        temp_local_dir (str): pathname to look into
    Returns:
        keys list (list): list of all unique keys found in h5 files in temp_local_dir"""
    files_ext= temp_local_dir +"/"+"*.h5" 
    temp_files = glob.glob(files_ext)
    all_keys = []
    for file in temp_files:
        keys = get_keys(file)
        for key in keys:
            all_keys.append(key)
    return list(set(all_keys))

def get_files_by_key(temp_local_dir, keys_list):
    """Looks through a direcotry and generates a dictionary of pandas dataframes that are separated by key value
    Args:
        temp_local_dir (str): directory to search through
        keys_list (list): list of key names (strings) to extract dataframes from each h5 file in the temp_local_dir

    Returns:
        df_dict (dict): Python dictionary of dataframes, organized by the h5 file key names
    """
    files_ext= temp_local_dir +"/"+"*.h5" 
    temp_files = glob.glob(files_ext)
    df_dict = {}
    for i, key in enumerate(keys_list):
        df_list = []
        for file in temp_files:
            f = h5py.File(file, 'r')
            file_keys = list(f.keys())
            for file_key in file_keys:
                if file_key==key:
                    df = open_file(file, h5_key=key)
                    df_list.append(df)
                else:
                    pass
        df_dict[key] = df_list
    return df_dict

def consolidate_and_move_files(dfdict: dict,  perm_path: str) -> list:
    """Takes in a python dictionary of pandas dataframes organized by key names, combines all dataframes into a single h5 
    and saves to permanent location
    Args:
        dfdict (dict): dictionary of pandas dataframes. Key names are the keys that will define the groups in the h5
        perm_path (str): directory where consolidated h5 file will be stored. (QNAS)
    Returns:
        Returns list of all dataframes found in the dfdict
        """
    dflist =[]
    for key, val in dfdict.items():
        df = pd.concat(val)
        dflist.append(df)
        df.to_hdf(perm_path, key=key, mode='a')
    return dflist

def save_permanent(temp_local_dir: str, permpath: str) -> None:
    """This method combines multiple methods. Takes in the temporary local directory to which chunked data has been saved, 
    looks for dataframes of the same key, combines those dataframes, and saves everything as a single H5 file in a permanent location"""
    keys = get_unique_keys(temp_local_dir)
    dfdict = get_files_by_key(temp_local_dir, keys)
    consolidate_and_move_files(dfdict, permpath)
