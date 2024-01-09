r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
Virtual Rainforest. Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapor exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly. Under steady-state,
the balance equation for the leaves in each canopy layer is as follows:

.. math::
    R_{abs} - R_{em} - H - \lambda E
    = R_{abs} - \epsilon_{s} \sigma T_{L}^{4} - c_{P}g_{Ha}(T_{L} - T_{A})
    - \lambda g_{v} \frac {e_{L} - e_{A}}{p_{A}} = 0

where :math:`R_{abs}` is absorbed radiation, :math:`R_{em}` emitted radiation, :math:`H`
the sensible heat flux, :math:`\lambda E` the latent heat flux, :math:`\epsilon_{s}` the
emissivity of the leaf, :math:`\sigma` the Stefan-Boltzmann constant, :math:`T_{L}` the
absolute temperature of the leaf, :math:`T_{A}` the absolute temperature of the air
surrounding the leaf, :math:`\lambda` the latent heat of vaporisation of water,
:math:`e_{L}` the effective vapour pressure of the leaf, :math:`e_{A}` the vapor
pressure of air and :math:`p_{A}` atmospheric pressure. :math:`g_{Ha}` is the heat
conductance between leaf and atmosphere, :math:`g_{v}` represents the conductance
for vapor loss from the leaves as a function of the stomatal conductance.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a linearisation approach to solve the equation for
leaf temperature and air temperature simultaneously, see
:cite:t:`maclean_microclimc_2021`.

In the soil, heat storage is almost always significant. Thus, Fourier's Law is combined
with the continuity equation to obtain a time dependant differential equation that
describes soil temperature as a function of depth and time. A numerical solution can be
achieved by dividing the soil into discrete layers. Each layer is assigned a node,
:math:`i`, at depth, :math:`zi`, and with heat storage, :matha;`C_{h_{i}}`, and nodes
are numbered sequentially downward such that node :math:`i+1` represents the
node for the soil layer immediately below. Conductivity, :math:`k_{i}`, represents
conductivity between nodes :math:`i` and :math:`i+1`. The energy balance equation for
node :math:`i` is then given by

.. math::
    \kappa_{i}(T_{i+1} - T_{i})- \kappa_{i-1}(T_{i} - T_{i-1})
    = \frac{C_{h_{i}}(T_{i}^{j+1} - T_{i}^{j})(z_{i+1} - z_{i-1})}{2 \Delta t}

where \Delta t is the time increment, conductance,
:math:`\kappa_{i}=k_{i}/(z_{i+1} - z_{i})`,  and superscript :math:`j` indicates the
time at which temperature is determined. This equation can be re-arranged and solved for
:math:`T_{j+1}` by Gaussian elimination using the Thomas algorithm.
"""  # noqa: D205, D415
