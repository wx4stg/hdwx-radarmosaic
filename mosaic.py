#!/usr/bin/env python3
#  Next-gen HDWX radar mosaic script by Sam Gardner <stgardner4@tamu.edu>
# Created 8 May 2021
from datetime import datetime as dt
import pytz
from matplotlib import pyplot as plt
import pyart
import cartopy.crs as ccrs
import cartopy.feature as cfeat
from metpy.plots import ctables
from matplotlib import colors as mplc
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from os import getcwd, path, listdir
# import asyncio


# async def readFile(radarFileName):
#     radarFilePath = path.join(radarDataDir, radarFileName)
#     radar = await pyart.io.read(radarFilePath, field_names={"REF" : "reflectivity"})
#     radar = radar.extract_sweeps([0])
#     if "reflectivity" in radar.fields:
#         radarsToPlot.append(radar)
#         radar_filtered = pyart.filters.GateFilter(radar)
#         radar_filtered.exclude_masked("reflectivity")
#         radar_filtered.exclude_invalid("reflectivity")
#         gateFilters.append(radar_filtered)

# async def asyncWrapper(contentsOfRadarDataDir):
#     tasks = [readFile(radarFileName) for radarFileName in sorted(contentsOfRadarDataDir)]
#     await asyncio.wait(tasks)

if __name__ == "__main__":
    start_exec = dt.now()
    px = 1/plt.rcParams['figure.dpi']
    fig = plt.figure()
    fig.set_size_inches(1880*px, 1025*px)
    time = dt.utcnow().replace(tzinfo=pytz.UTC)
    radarsToPlot = []
    gateFilters = []
    radarDataDir = path.join(getcwd(), "radarData")
    print("Reading files...")
    for radarFileName in listdir(radarDataDir):
        radarFilePath = path.join(radarDataDir, radarFileName)
        radar = pyart.io.read(radarFilePath)
        radar = radar.extract_sweeps([0])
        for field in radar.fields.copy():
            if field != "reflectivity":
                radar.fields.pop(field)
        if "reflectivity" in radar.fields:
            radarsToPlot.append(radar)
            radar_filtered = pyart.filters.GateFilter(radar)
            radar_filtered.exclude_masked("reflectivity")
            radar_filtered.exclude_invalid("reflectivity")
            gateFilters.append(radar_filtered)
    radarsToPlot = tuple(radarsToPlot)
    gateFilters = tuple(gateFilters)
    print("Gridding...")
    print(dt.now() - start_exec)
    grids = pyart.map.grid_from_radars(radarsToPlot,
        (16,1600,1600),
        ((0.,15000.),(-1567000.,1567000.),(-2931500.,2931500.)),
        weighting_function="nearest",
        fields=['reflectivity'],
        gatefilters=gateFilters,
        grid_origin=(39.83333, -98.58333)
        )
    print("Plotting...")
    print(dt.now() - start_exec)
    xgrids = grids.to_xarray()
    ax = plt.axes(projection=ccrs.AzimuthalEquidistant(central_latitude=grids.get_projparams()["lat_0"], central_longitude=grids.get_projparams()["lon_0"]))
    ax.add_feature(cfeat.STATES)
    ax.add_feature(cfeat.COASTLINE)
    ax.axis("off")
    # local ax.set_extent([-100.65, -93, 28.6, 32.5])
    # regional ax.set_extent([-110, -85, 23.5, 36.600704])
    # national ax.set_extent([-124.848974, -66.885444, 23.5, 49])
    ax.set_extent([-124.848974, -66.885444, 21, 49])
    cmap = ctables.registry.get_colortable('NWSReflectivity')
    cmap.set_under("#00000000")
    cmap.set_over("black")
    norm = mplc.Normalize(vmin=5, vmax=90)
    pc = xgrids.reflectivity.sel(z=0, time=xgrids.time[0], method="nearest").plot.pcolormesh(norm=norm, cmap=cmap, ax=ax, add_colorbar=False)
    ax.set_title("")
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    fig.savefig("mosaic.png", bbox_inches=extent, transparent=True)
    divider = make_axes_locatable(ax)
    insAx = inset_axes(ax, width="50%", height="5%", loc="lower left")
    cb = fig.colorbar(pc, cax=insAx, orientation="horizontal")
    insAx.set_xlabel("Reflectivity (dBZ)", backgroundcolor="white", labelpad=1)
    fig.set_facecolor("white")
    fig.savefig("fullFig.png")
    print("Done!")
    print(dt.now() - start_exec)
