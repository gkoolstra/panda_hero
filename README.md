# Kungfu Pandas Tools
Simple tool set for saving pandas datasets. Simple use cases: 

## Create a path filename
If chip info yaml path is included, chip ID will be added to filename
```
chip_info_path = r'/Volumes/EeroQ/Projects/004_Device2.0/config/chipinfo_v241.yaml'
filepath = kp.create_path_filename(measurement_name='1dsweep', path= None, chip_info_path = chip_info_path)
```

## Save a 1d sweep
```
fpoints = np.linspace(1, 9, 101)
mag = np.random.rand(101)
phase = np.random.rand(101)

save_nd_sweep(filepath=filepath, data_array=np.c_[mag, phase], data_column_names=["magnitude", "phase"], 
              index_arrays=[fpoints], index_names=["fpoints"], 
              h5_key="vna_spectrum")
```

## Build a 2d data set
Simulate a sweep over some arrays x1 and x2 (as one would do in experiment). Then generate some fake data point with 3 quantities, imagine these are the freq, mag, phase from a VNA trace at a single frequency.
```
# x1 and x2 are imaginary voltage sweep axes
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

## Save and append to dictionaries
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



## Chunk a datafile
Opening large files (>10 MB) while incrementally saving data to the NAS can be time consuming and slow down the data acquisition process. 
Chunking allows users to check the working file size each time data is saved. If the current working filepath contains too much data, a new filepath is generated and data is saved there instead.
Follow the steps below when chunking.

```
# Generate a directory where chunked files will be saved
measurement_name = 'chunked_measurement'
local_dir = '/Users/eeroq1/data'
chip_info_path = '/Users/eeroq/Documents/v41_dev.yaml'
temp_local_dir = kp.create_temp_dir(measurement_name = measurement_name , local_dir = local_dir, chip_info_path: '/Users/eeroq/Documents/v41_dev.yaml')

# Generate a working filepath to save data to. 
filepath = kp.get_working_temp_file(temp_local_dir = temp_local_dir, chip_info_path= chip_info_path)
```
Once an initial filepath has been generated, data can be saved to that path. File size checking should occur somewhere in the data acquisition code: 
```
#Check that the current working file is smaller than the indicated file size in bytes. If it is larger, the filepath is updated.
max_filesize = 5e6 
filepath = kp.check_filesize(filepath, max_filesize)
```




