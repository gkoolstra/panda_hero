# Panda Hero

![](/images/cover_image.png)

Panda Hero is a simple tool set for saving pandas datasets, which can handle multi-variable parameter sweeps. The advantage of this tool is that the resulting pandas dataframe objects can be easily opened, and viewed in a jupyter notebook. All standard pandas manipulation techniques can be used on datasets. There are a few simple use cases discussed below to help you get started with Kungfu Pandas. To get started use this:

```
from panda_hero import kungfu_pandas as kp
```

## Automatic data organization with Panda Hero
### Vanilla
Setting up your filepath is the first step for every experiment. We use the following subfolder convention for organizing data:
`path > [yyyy-mm-dd] > [yyyy-mm-dd_hh-mm-ss_measurement_name.h5]`

By supplying `path` to `create_path_filename` the subfolders are automatically generated. Easy!
```
filepath = kp.create_path_filename(measurement_name=..., path=...)
```

### With a file containing chip information
However, additional info about the device and measurement is often provided in `chip_info_path`, which is a yaml file containing keys such as setup and chip_ID. If provided, a new subfolder will be added to allow for multiple setups saving in the same directory, and a chip ID will be added to the h5 filename. In this case we have the following path organization:
`path > [yyyy-mm-dd] > [setup] > [yyyy-mm-dd_hh-mm-ss_chipID_measurement_name.h5]`

Usage example: the following code snippet
```
chip_info_path = r'Z:/Projects/011_Device3.0/config/chipinfo_hamburger_cell.yaml'
data_path = r'Z:/Projects/011_Device3.0/data'
measurement_name = 'close_the_dot'

filepath = kp.create_path_filename(measurement_name=measurement_name, path=data_path, chip_info_path=chip_info_path)
```
will result in the following file structure
![Datafolder structure in Panda Hero](/images/path_organization.png)

## Example: Save a 1D sweep
For simple experiments such as 
- Simple VNA scan with only one trace. Each frequency point is only related to one magnitude and one phase point.

Example usage:
```
fpoints = np.linspace(1, 9, 101)
mag = np.random.rand(101)
phase = np.random.rand(101)

save_nd_sweep(filepath=filepath, data_array=np.c_[mag, phase], data_column_names=["magnitude", "phase"], 
              index_arrays=[fpoints], index_names=["fpoints"], 
              h5_key="vna_spectrum")
```

## Example: Build a multi-indexed data set
For more complicated experiments such as 
- Repeated VNA scans as function of voltage. 
- Power sweeps, temperature sweeps, etc.
- Very complicated sweeps with any number of sweep variables

Example usage:
Imagine an experiment where you sweep over arrays x1 and x2 while recording 3 quantities (in `data_array`). You could imagine these are the freq, mag, phase from a VNA trace.
```
x1 = np.linspace(0, 0.5, 21)
x2 = np.linspace(0.5, -0.5, 11)

for X1 in x1:
    for X2 in x2:
        data_array = np.random.rand(10, 3)
        
        kp.append_nd_sweep(filepath, data_array, index_arrays=[[X1], [X2], range(10)], 
                           data_column_names=["a", "b", "c"], 
                           index_names=["x1", "x2", "fpoints"], 
                           h5_key="build3d")
```

Some helpful hints:
- `index_names` must be a list with the same number of elements as `index_arrays`
- All elements in `index_arrays` must have a length (they can't be floats). 
- The number of `data_column_names` must match the second dimension of `data_array`
- You can create an entirely different group in the same datafile by supplying a different `h5_key`. 

## Example: Save and append to dictionaries
For keeping track of settings stored in a dictionary form.
```
# Create a dictionary with some settings
settings = {"setting_1" : 3.0, "setting_2" : True, "setting_3" : "another_datatype"}

kp.save_dict(filepath=filepath, data_dict=settings, h5_key="settings")
```
Append to the same dictionary with more data:
```
more_settings = {"setting_1" : 1.0, "setting_2" : False, "setting_3" : "test1"}
kp.append_dict(filepath, more_settings, h5_key="settings")
```



## Big data files: chunking
Opening large files (>10 MB) while incrementally saving data to network locations can be time consuming and slow down the data acquisition process. 
Chunking allows users to check the working file size each time data is saved. If the current data file exceeds a user defined maximum size, a new filepath is generated and data is saved there instead.

Please follow the steps below to use chunking.

```
# Generate a directory where chunked files will be saved. For optimal speed, this directory should not be on a network. 
measurement_name = 'chunked_measurement'
local_dir = '/Users/eeroq1/data'
chip_info_path = '/Users/eeroq/Documents/v41_dev.yaml'

# This is a local (non-network) directory, not a filepath
temp_local_dir = kp.create_temp_dir(measurement_name=measurement_name, local_dir=local_dir, chip_info_path=chip_info_path)

# Generate a working filepath, i.e. subfolder, for saving the data. 
filepath = kp.get_working_temp_file(temp_local_dir=temp_local_dir, chip_info_path=chip_info_path)
```

Once an initial filepath has been generated, data can be saved to that path. File size checking should occur periodically (e.g. each iteration of a `for`-loop) in the data acquisition code: 

```
filepath = kp.check_filesize(filepath, max_filesize=5e6)
```

Finally, at the end of the measurement, we run the following piece of code
```
# Consolidate file chunks
out_file = os.path.join(temp_local_dir, f"{os.path.split(temp_local_dir)[-1]}_consolidated.h5")
kp.save_permanent(temp_local_dir, out_file)

dest = os.path.join(permanent_datapath, os.path.split(out_file)[-1])
shutil.copy(out_file, dest)
```


