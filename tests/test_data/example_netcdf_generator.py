"""Generate NetCDF datasets for testing."""


def generate_files() -> None:
    """Generates a set of test files for test_data."""

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
    cell_id = np.arange(x_n * y_n)

    # Simple constant data to facilitate checksum in tests
    grid_size = (x_n, y_n)
    temp = np.ones(grid_size) * 20

    # Some shared modifiers
    temp_flat = temp.flatten()
    too_few = np.arange(60)  # Cellid dimension subset
    sset = np.arange(6)  # XY dimension subset

    # ----------------------------------------------------------------------
    # Generate unhandled file format
    # ----------------------------------------------------------------------
    with open("this_data_format.not_handled", "w") as outf:
        outf.write("This file format cannot be read")

    # ----------------------------------------------------------------------
    # Generate garbage netcdf file
    # ----------------------------------------------------------------------
    with open("garbage.nc", "w") as outf:
        outf.write("This is not the NetCDF file you are looking for")

    # ----------------------------------------------------------------------
    # Generate NetCDF with cell_id dimension
    # ----------------------------------------------------------------------

    # Good version
    ds_1cid = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp_flat, dims=["cell_id"]),
        }
    )

    ds_1cid.to_netcdf("cellid_dims.nc")

    # Bad version - doesn't cover cells
    ds_1cid_too_few = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp_flat[too_few], dims=["cell_id"]),
        }
    )

    ds_1cid_too_few.to_netcdf("cellid_dim_too_few.nc")

    # Bad version - too many cells and no ids
    ds_1cid_too_many = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                np.concatenate((temp_flat, temp_flat)), dims=["cell_id"]
            ),
        }
    )

    ds_1cid_too_many.to_netcdf("cellid_dim_too_many.nc")

    # ----------------------------------------------------------------------
    # Generate NetCDF with cell_id coordinates
    # ----------------------------------------------------------------------

    # Good version

    ds_1cid = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                temp.flatten(), coords=[cell_id], dims=["cell_id"]
            ),
        }
    )

    ds_1cid.to_netcdf("cellid_coords.nc")

    # Bad version - doesn't cover cells

    ds_1cid_too_few = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                temp.flatten()[too_few], coords=[cell_id[too_few]], dims=["cell_id"]
            ),
        }
    )

    ds_1cid_too_few.to_netcdf("cellid_coords_too_few.nc")

    # Bad version - numbering incorrect

    ds_1cid_badid = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(
                temp.flatten(), coords=[cell_id + 100], dims=["cell_id"]
            ),
        }
    )

    ds_1cid_badid.to_netcdf("cellid_coords_bad_cellid.nc")

    # ----------------------------------------------------------------------
    # Generate NetCDF with 2D grid with no coordinates on dimension
    # ----------------------------------------------------------------------

    # - Good version
    ds_2idx = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp, dims=["x", "y"]),
        }
    )

    ds_2idx.to_netcdf("xy_dim.nc")

    # - bad: extent too small

    ds_2idx_small = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp[sset], dims=["x", "y"]),
        }
    )

    ds_2idx_small.to_netcdf("xy_dim_small.nc")

    # - bad: extent too large

    ds_2idx_large = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(np.concatenate((temp, temp)), dims=["x", "y"]),
        }
    )

    ds_2idx_large.to_netcdf("xy_dim_large.nc")

    # ----------------------------------------------------------------------
    # Generate NetCDF with 2D grid with actual coordinates on dimensions
    # ----------------------------------------------------------------------

    # - good version.
    ds_2xy = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp, coords=[x, y], dims=["x", "y"]),
        }
    )

    ds_2xy.to_netcdf("xy_coords.nc")

    # - bad: does not cover all cells
    ds_2xy_6by10 = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp[sset], coords=[x[sset], y], dims=["x", "y"]),
        }
    )

    ds_2xy_6by10.to_netcdf("xy_coords_small.nc")

    # - bad: coordinates don't match

    ds_2xy_lowx = xarray.Dataset(
        data_vars={
            "temp": xarray.DataArray(temp, coords=[x - 3e6, y], dims=["x", "y"]),
        }
    )

    ds_2xy_lowx.to_netcdf("xy_coords_shifted.nc")

    # # ----------------------------------------------------------------------
    # # Generate NetCDF with column data with a row dimension integer, including x and y
    # # data (A data frame, basically)
    # # ----------------------------------------------------------------------

    # # Good version
    # ds_df = xarray.Dataset(
    #     data_vars={
    #         "temperature": xarray.DataArray(temp.flatten(), dims=["row"]),
    #         "precipitation": xarray.DataArray(prec.flatten(), dims=["row"]),
    #         "x": xarray.DataArray(xx.flatten(), dims=["row"]),
    #         "y": xarray.DataArray(yy.flatten(), dims=["row"]),
    #     }
    # )

    # ds_df.to_netcdf("one_dim_points_xy.nc")

    # # Bad version - x and y don't align

    # ds_df_xney = xarray.Dataset(
    #     data_vars={
    #         "temperature": xarray.DataArray(temp.flatten(), dims=["row"]),
    #         "precipitation": xarray.DataArray(prec.flatten(), dims=["row"]),
    #         "x": xarray.DataArray(xx.flatten()[0:60], dims=["row_short"]),
    #         "y": xarray.DataArray(yy.flatten(), dims=["row"]),
    #     }
    # )

    # ds_df_xney.to_netcdf("one_dim_points_xy_xney.nc")

    # # Bad version - doesn't cover cells

    # lown = np.arange(60)

    # ds_1cid_lown = xarray.Dataset(
    #     data_vars={
    #         "temp": xarray.DataArray(
    #             temp.flatten()[lown], coords=[cell_id[lown]], dims=["row"]
    #         ),
    #         "prec": xarray.DataArray(
    #             prec.flatten()[lown], coords=[cell_id[lown]], dims=["row"]
    #         ),
    #         "x": xarray.DataArray(xx.flatten()[lown], dims=["row"]),
    #         "y": xarray.DataArray(yy.flatten()[lown], dims=["row"]),
    #     }
    # )

    # ds_df_xney.to_netcdf("one_dim_points_xy_lown.nc")

    # # ----------------------------------------------------------------------
    # # Generate NetCDF with column data with a row_idx dimension integer, _not_
    # # including x and y data (A data frame, basically, but with an assumed order).
    # # ----------------------------------------------------------------------

    # ds_df = xarray.Dataset(
    #     data_vars={
    #         "temperature": xarray.DataArray(temp.flatten(), dims=["cell_id"]),
    #         "precipitation": xarray.DataArray(prec.flatten(), dims=["cell_id"]),
    #     }
    # )

    # ds_df.to_netcdf("one_dim_points_order_only.nc")


if __name__ == "__main__":

    generate_files()
