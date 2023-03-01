import xarray as xr


@xr.register_dataarray_accessor("writable")
class WritableArray:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._flag = xarray_obj.data.flags["WRITEABLE"]

    def __enter__(self):
        self._obj.data.setflags(write=True)
        return self._obj

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._obj.data.setflags(write=self._flag)


if __name__ == "__main__":
    import numpy as np

    T = xr.DataArray(np.ones(3))
    T.data.setflags(write=False)

    try:
        T[1] = 42
    except:
        print("T is not writable!")

    with T.writable:
        T[1] = 42
        print("Now it is writable.")

    try:
        T[0] = 42
    except:
        print("T is not writable... again!")
    
    print(T)
