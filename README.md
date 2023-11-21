# Kungfu Pandas Tools
Simple tool set for saving pandas datasets. Simple use cases: 

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