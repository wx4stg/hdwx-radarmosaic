#!/usr/bin/env python3
# Next-gen HDWX radar mosaic script
# Created 8 May 2021 by Sam Gardner <stgardner4@tamu.edu>
from datetime import datetime as dt
import pytz
from matplotlib import pyplot as plt
import pyart
import cartopy.crs as ccrs
import cartopy.feature as cfeat
from metpy.plots import ctables
from metpy.plots import USCOUNTIES
from matplotlib import colors as mplc
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from matplotlib import image as mpimage
from os import getcwd, path, listdir
import sys

if __name__ == "__main__":
    start_exec = dt.now()
    px = 1/plt.rcParams["figure.dpi"]
    basePath = path.join(getcwd(), "output")
    fig = plt.figure()
    fig.set_size_inches(1.227*1880*px, 1.217*1025*px)
    time = dt.utcnow().replace(tzinfo=pytz.UTC)
    radarsToPlot = []
    gateFilters = []
    radarDataDir = path.join(getcwd(), "radarData")
    for radarFileName in listdir(radarDataDir):
        radarFilePath = path.join(radarDataDir, radarFileName)
        try:
            radar = pyart.io.read(radarFilePath)
        except Exception as e:
            warningString = str(dt.utcnow())+" error reading "+radarFileName+": "+str(e)+"\n"
            logFile = open("warnings.log", "a")
            logFile.write(warningString)
            logFile.close()
            continue
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
    if sys.argv[1] == "local":
        gridExtent = ((0.,1.),(-220000.,220000.),(-375000.,375000.))
        gridOrig = (30.55, -97.825)
        axExtent = [-101.65, -94, 28.6, 32.5]
        titleStr = "Local Radar Mosaic"
        featLinewidth = 4
        saveDir = "radar/local/"
    elif sys.argv[1] == "regional":
        gridExtent = ((0.,1.),(-860000.,860000.),(-1272000.,1272000.))
        gridOrig = (30.05, -97.5)
        axExtent = [-110, -85, 23.5, 36.600704]
        titleStr = "Regional Radar Mosaic"
        featLinewidth = 3
        saveDir = "radar/regional/"
    elif sys.argv[1] == "national":
        gridExtent = ((0.,1.),(-1567000.,1567000.),(-2931500.,2931500.))
        gridOrig = (39.83333, -98.58333)
        axExtent = [-124.848974, -66.885444, 22, 48]
        titleStr = "National Radar Mosaic"
        featLinewidth = 1
        saveDir = "radar/national/"
    classicSavePath = path.join(path.join(basePath, "products"), saveDir)
    gisSavePath = path.join(path.join(basePath, "gisproducts"), saveDir)
    grids = pyart.map.grid_from_radars(radarsToPlot,
        (1,1600,1600),
        gridExtent,
        weighting_function="nearest",
        fields=["reflectivity"],
        gatefilters=gateFilters,
        grid_origin=gridOrig
        )
    xgrids = grids.to_xarray()
    ax = plt.axes(projection=ccrs.AzimuthalEquidistant(central_latitude=grids.get_projparams()["lat_0"], central_longitude=grids.get_projparams()["lon_0"]))
    ax.set_extent(axExtent)
    if  sys.argv[1] == "regional":
        ax.add_feature(USCOUNTIES.with_scale("5m"), edgecolor="green")
    elif sys.argv[1] == "local":
        ax.add_feature(USCOUNTIES.with_scale("5m"), edgecolor="green")
        roads = cfeat.NaturalEarthFeature("cultural", "roads_north_america", "10m", facecolor="none")
        ax.add_feature(roads, edgecolor="red")
    ax.add_feature(cfeat.STATES, linewidth=featLinewidth)
    ax.add_feature(cfeat.COASTLINE, linewidth=featLinewidth)
    plt.setp(ax.spines.values(), visible=False)
    norm, cmap = ctables.registry.get_with_steps("NWSReflectivity", 10, 5)
    cmap.set_under("#00000000")
    cmap.set_over("black")
    pc = xgrids.reflectivity.sel(z=0, time=xgrids.time[0], method="nearest").plot.pcolormesh(norm=norm, cmap=cmap, ax=ax, add_colorbar=False, zorder=0)
    ax.set_title("")
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(path.join(gisSavePath, "frame9.png"), bbox_inches=extent, transparent=True)
    cbax = fig.add_axes([ax.get_position().x0,0.075,(ax.get_position().width/3),.02])
    cb = fig.colorbar(pc, cax=cbax, orientation="horizontal", extend="neither")
    cbax.set_xlabel("Reflectivity (dBZ)")
    tax = fig.add_axes([ax.get_position().x0+cbax.get_position().width+.01,0.045,(ax.get_position().width/3),.05])
    timeOfPull = dt(time.year, time.month, time.day, time.hour, int(sys.argv[2]), 0)
    timeStr = timeOfPull.strftime("Valid %-d %b %Y %H%MZ")
    tax.text(0.5, 0.5, titleStr+"\n"+timeStr, horizontalalignment="center", verticalalignment="center", fontsize=16)
    tax.set_xlabel("Python HDWX -- Send bugs to stgardner4@tamu.edu")
    plt.setp(tax.spines.values(), visible=False)
    tax.tick_params(left=False, labelleft=False)
    tax.tick_params(bottom=False, labelbottom=False)
    lax = fig.add_axes([ax.get_position().x0+cbax.get_position().width+tax.get_position().width+.01,0,(ax.get_position().width/3),.1])
    lax.set_aspect(2821/11071)
    lax.axis("off")
    plt.setp(lax.spines.values(), visible=False)
    atmoLogo = mpimage.imread("assets/atmoLogo.png")
    lax.imshow(atmoLogo)
    fig.set_facecolor("white")
    fig.savefig(path.join(classicSavePath, "frame9.png"), bbox_inches="tight")

