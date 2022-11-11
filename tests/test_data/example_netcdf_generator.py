"""Generate NetCDF datasets for testing."""


def generate_files() -> None:
    """Generates a set of test files for test_data."""

    from itertools import product

    import numpy as np
    import xarray

    # https://towardsdatascience.com/basic-data-structures-of-xarray-80bab8094efa

    x_n = 10
    y_n = 10
    res = 100
    x_off = 500000
    y_off = 200000

    # Row and column indices
    x_idx = np.arange(x_n)
    y_idx = np.arange(y_n)

    # Cell centre coordinates
    x = x_off + x_idx * res + res / 2
    y = y_off + y_idx * res + res / 2

    xx, yy = np.meshgrid(x, y)

    # Cell IDs
    cell_id = np.array([f"{x}-{y}" for x, y in product(x_idx, y_idx)])

    # Some data
    rng = np.random.default_rng()

    grid_size = (x_n, y_n)

    temp = rng.normal(loc=20, scale=3, size=grid_size)
    prec = rng.lognormal(mean=5, sigma=1, size=grid_size)

    # ----------------------------------------------------------------------
    # Generate NetCDF with 2D grid with actual coordinates on dimensions
    # ----------------------------------------------------------------------

    # - good version.
    ds_2xy = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp, coords=[x, y], dims=["x", "y"]),
            "prec": xarray.DataArray(prec, coords=[x, y], dims=["x", "y"]),
        }
    )

    ds_2xy.to_netcdf("two_dim_xy.nc")

    # - bad: extent not x_n by y_n
    sset = np.arange(6)

    ds_2xy_6by10 = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp[sset], coords=[x[sset], y], dims=["x", "y"]),
            "prec": xarray.DataArray(prec[sset], coords=[x[sset], y], dims=["x", "y"]),
        }
    )

    ds_2xy_6by10.to_netcdf("two_dim_xy_6by10.nc")

    # - bad: coordinates don't match

    ds_2xy_lowx = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp, coords=[x - 3e6, y], dims=["x", "y"]),
            "prec": xarray.DataArray(prec, coords=[x - 3e6, y], dims=["x", "y"]),
        }
    )

    ds_2xy_lowx.to_netcdf("two_dim_xy_lowx.nc")

    # ----------------------------------------------------------------------
    # Generate NetCDF with 2D grid with no coordinates on dimension
    # ----------------------------------------------------------------------

    # - Good version
    ds_2idx = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp, dims=["x", "y"]),
            "prec": xarray.DataArray(prec, dims=["x", "y"]),
        }
    )

    ds_2idx.to_netcdf("two_dim_idx.nc")

    # - bad: extent not x_n by y_n
    sset = np.arange(6)

    ds_2idx_6by10 = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp[sset], coords=[x[sset], y], dims=["x", "y"]),
            "prec": xarray.DataArray(prec[sset], coords=[x[sset], y], dims=["x", "y"]),
        }
    )

    ds_2idx_6by10.to_netcdf("two_dim_idx_6by10.nc")

    # ----------------------------------------------------------------------
    # Generate NetCDF with column data indexed by cell id - if we use an integer cell id
    # then this collapses to the example dataframe with assumed order?
    # ----------------------------------------------------------------------

    # Good version

    ds_1cid = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                temp.flatten(), coords=[cell_id], dims=["cell_id"]
            ),
            "prec": xarray.DataArray(
                prec.flatten(), coords=[cell_id], dims=["cell_id"]
            ),
        }
    )

    ds_1cid.to_netcdf("one_dim_cellid.nc")

    # Bad version - doesn't cover cells
    lown = np.arange(60)

    ds_1cid_lown = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                temp.flatten()[lown], coords=[cell_id[lown]], dims=["cell_id"]
            ),
            "prec": xarray.DataArray(
                prec.flatten()[lown], coords=[cell_id[lown]], dims=["cell_id"]
            ),
        }
    )

    ds_1cid_lown.to_netcdf("one_dim_cellid_lown.nc")

    # Bad version - IDs don't match
    cell_id_no = np.char.add(cell_id, ["no!"])

    ds_1cid_badid = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                temp.flatten(), coords=[cell_id_no], dims=["cell_id"]
            ),
            "prec": xarray.DataArray(
                prec.flatten(), coords=[cell_id_no], dims=["cell_id"]
            ),
        }
    )

    ds_1cid_badid.to_netcdf("one_dim_cellid_badid.nc")

    # ----------------------------------------------------------------------
    # Generate NetCDF with column data with a row dimension integer, including x and y
    # data (A data frame, basically)
    # ----------------------------------------------------------------------

    # Good version
    ds_df = xarray.Dataset(
        data_vars={
            "temperature": xarray.DataArray(temp.flatten(), dims=["row"]),
            "precipitation": xarray.DataArray(prec.flatten(), dims=["row"]),
            "x": xarray.DataArray(xx.flatten(), dims=["row"]),
            "y": xarray.DataArray(yy.flatten(), dims=["row"]),
        }
    )

    ds_df.to_netcdf("one_dim_points_xy.nc")

    # Bad version - x and y don't align

    ds_df_xney = xarray.Dataset(
        data_vars={
            "temperature": xarray.DataArray(temp.flatten(), dims=["row"]),
            "precipitation": xarray.DataArray(prec.flatten(), dims=["row"]),
            "x": xarray.DataArray(xx.flatten()[0:60], dims=["row_short"]),
            "y": xarray.DataArray(yy.flatten(), dims=["row"]),
        }
    )

    ds_df_xney.to_netcdf("one_dim_points_xy_xney.nc")

    # Bad version - doesn't cover cells

    lown = np.arange(60)

    ds_1cid_lown = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                temp.flatten()[lown], coords=[cell_id[lown]], dims=["row"]
            ),
            "prec": xarray.DataArray(
                prec.flatten()[lown], coords=[cell_id[lown]], dims=["row"]
            ),
            "x": xarray.DataArray(xx.flatten()[lown], dims=["row"]),
            "y": xarray.DataArray(yy.flatten()[lown], dims=["row"]),
        }
    )

    ds_df_xney.to_netcdf("one_dim_points_xy_lown.nc")

    # ----------------------------------------------------------------------
    # Generate NetCDF with column data with a row_idx dimension integer, _not_ including
    # x and y data (A data frame, basically, but with an assumed order).
    # ----------------------------------------------------------------------

    ds_df = xarray.Dataset(
        data_vars={
            "temperature": xarray.DataArray(temp.flatten(), dims=["cell_id"]),
            "precipitation": xarray.DataArray(prec.flatten(), dims=["cell_id"]),
        }
    )

    ds_df.to_netcdf("one_dim_points_order_only.nc")


if __name__ == "__main__":

    generate_files()
