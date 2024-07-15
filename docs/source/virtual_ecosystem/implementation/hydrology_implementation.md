# Implementation of the Hydrology Model

The [hydrology](../../api/models/hydrology.md) model simulates the hydrological
processes in the Virtual Ecosystem. We placed hydrology in a separate model to allow
easy replacement with a different hydrology model. Also, this separation provides more
flexibility in defining the order of models an/or processes in the overall Virtual
Ecosystem workflow.

```{note}
Some of the features described here are not yet implemented.
```

## Vertical hydrology components

The vertical component of the hydrology model determines the water balance within each
grid cell. This includes [above ground](../../api/models/hydrology/above_ground.md)
processes such as rainfall, intercept, and surface runoff out of the grid cell.
The [below ground](../../api/models/hydrology/below_ground.md) component considers
infiltration, bypass flow, percolation (= vertical flow), soil moisture and matric
potential, horizontal sub-surface flow out of the grid cell, and changes in
groundwater storage.
The model is loosely based on the LISFLOOD model {cite}`van_der_knijff_lisflood_2010`.

## Horizontal hydrology components

The second part of the hydrology model calculates the horizontal water movement across
the full model grid including accumulated surface runoff and sub-surface flow, and river
discharge rate, [see](../../api/models/hydrology/above_ground.md). The flow direction is
based on a digital elevation model.
