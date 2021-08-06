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
from matplotlib import image as mpimage
from os import path, listdir
from pathlib import Path
import sys
import json

def writeJson(productID, doesSupportGIS):
    if doesSupportGIS:
        gisInfo = [str(axExtent[2])+","+str(axExtent[0]), str(axExtent[3])+","+str(axExtent[1])]
    else:
        gisInfo = ["0,0", "0,0"]
    productFrameDict = {
        "fhour" : 0,
        "filename" : saveFileName+".png",
        "gisInfo" : gisInfo,
        "valid" : validInt
    }
    jsonPath = path.join(path.join(tmpFrameMetaStorage, timeOfPull.strftime("%H")), str(productID))
    Path(jsonPath).mkdir(parents=True, exist_ok=True)
    jsonPath = path.join(jsonPath, saveFileName+".json")
    with open(jsonPath, "w") as fileToWrite:
        json.dump(productFrameDict, fileToWrite, indent=4)

if __name__ == "__main__":
    basePath = path.join(path.dirname(path.abspath(__file__)), "output")
    tmpFrameMetaStorage = path.join(path.dirname(path.abspath(__file__)), "frameMetaData/")
    Path(tmpFrameMetaStorage).mkdir(parents=True, exist_ok=True)
    radarDataDir = path.join(path.dirname(path.abspath(__file__)), "radarData")
    fig = plt.figure()
    px = 1/plt.rcParams["figure.dpi"]
    fig.set_size_inches(1.227*1880*px, 1.217*1025*px)
    time = dt.utcnow().replace(tzinfo=pytz.UTC)
    radarsToPlot = []
    gateFilters = []
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
    timeOfPull = dt(time.year, time.month, time.day, time.hour, int(sys.argv[2]), 0)
    runPathExtension = timeOfPull.strftime("%Y/%m/%d/%H00")
    validInt = int(timeOfPull.strftime("%Y%m%d%H%M"))
    if sys.argv[1] == "local":
        gisProductID = 0
        classicProductID = 1
        gridExtent = ((0.,1.),(-220000.,220000.),(-420000.,420000.))
        axExtent = [-101, -92.4, 28.6, 32.5]
        titleStr = "Local Radar Mosaic"
        featLinewidth = 4
        saveDir = path.join("radar/local/", runPathExtension)
    elif sys.argv[1] == "regional":
        gisProductID = 2
        classicProductID = 3
        gridExtent = ((0.,1.),(-860000.,860000.),(-1272000.,1272000.))
        axExtent = [-110, -85, 23.5, 37]
        titleStr = "Regional Radar Mosaic"
        featLinewidth = 3
        saveDir = path.join("radar/regional/", runPathExtension)
    elif sys.argv[1] == "national":
        gisProductID = 4
        classicProductID = 5
        gridExtent = ((0.,1.),(-1567000.,1567000.),(-2931500.,2931500.))
        axExtent = [-124.848974, -66.885444, 23, 48]
        titleStr = "National Radar Mosaic"
        featLinewidth = 1
        saveDir = path.join("radar/national/", runPathExtension)
    classicSavePath = path.join(path.join(basePath, "products"), saveDir)
    Path(classicSavePath).mkdir(parents=True, exist_ok=True)
    gisSavePath = path.join(path.join(basePath, "gisproducts"), saveDir)
    Path(gisSavePath).mkdir(parents=True, exist_ok=True)
    grids = pyart.map.grid_from_radars(radarsToPlot,
        (1,1600,1600),
        gridExtent,
        weighting_function="nearest",
        fields=["reflectivity"],
        gatefilters=gateFilters,
        grid_origin=((axExtent[2]+axExtent[3])/2, (axExtent[0]+axExtent[1])/2)
        )
    xgrids = grids.to_xarray()
    dataProj = ccrs.AzimuthalEquidistant(central_latitude=grids.get_projparams()["lat_0"], central_longitude=grids.get_projparams()["lon_0"])
    ax = plt.axes(projection=ccrs.epsg(3857))
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
    pc = xgrids.reflectivity.sel(z=0, time=xgrids.time[0], method="nearest").plot.pcolormesh(norm=norm, cmap=cmap, ax=ax, add_colorbar=False, zorder=0, transform=dataProj)
    ax.set_title("")
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    saveFileName = "frame"+str(int(timeOfPull.minute)/5).replace(".0", "")
    fig.savefig(path.join(gisSavePath, saveFileName+".png"), bbox_inches=extent, transparent=True)
    writeJson(gisProductID, True)
    cbax = fig.add_axes([ax.get_position().x0,0.075,(ax.get_position().width/3),.02])
    cb = fig.colorbar(pc, cax=cbax, orientation="horizontal", extend="neither")
    cbax.set_xlabel("Reflectivity (dBZ)")
    tax = fig.add_axes([ax.get_position().x0+cbax.get_position().width+.01,0.045,(ax.get_position().width/3),.05])
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
    fig.savefig(path.join(classicSavePath, saveFileName+".png"), bbox_inches="tight")
    writeJson(classicProductID, False)

