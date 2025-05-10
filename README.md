# ICON Grid renumbering

This project provides some functionalities to take an icosahedral grid, typically from the ICON model, extract the 10 rhomboids (5 on the North hemisphere and 5 on the South), and renumber then as two dimensional arrays. This enables the restructuring of the files into regular pieces that can then be processed as such, for data compression or even computation.

Example:
```python
import igutils
renum = igutils.RenumberedGridVertices("icon_grid_0013_R02B04_R.nc", verbose=True, skip_check=True)
renum.plot_rhomboid(renum.get_rhomboid_north(4))
```

The project uses `uv` for the setup.
