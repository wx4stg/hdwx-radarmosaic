import requests
import pandas as pd
import re
import sys
from nexradaws import NexradAwsInterface
from datetime import datetime as dt
import pytz
from os import getcwd, path

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def getRadarData(connex, site, targ):
    allScans = connex.get_avail_scans(targ.year, targ.month, targ.day, site)
    scanTimes = [scan.scan_time for scan in allScans]
    these_good_scans = []
    these_good_times = []
    for i in range(len(scanTimes)):
        if scanTimes[i] is not None:
            these_good_times.append(scanTimes[i])
            these_good_scans.append(allScans[i])
        else:
            print("Invalid time at index", i)
    this_nearest_time = nearest(these_good_times, targ)
    this_index = these_good_times.index(this_nearest_time)
    conn.download(these_good_scans[this_index], path.join(getcwd(), "radarData"))


if __name__ == "__main__":
    blackList = ["TJUA", "PABC", "PACG", "PAEC", "PAHG", "PAIH", "PAKC", "PAPD", "PGUA", "PHKI", "PHKM", "PHMO", "PHWA", "RKJK", "RKSG", "RODN"]
    if len(sys.argv) == 1:
        s = requests.get("https://radar2pub.ncep.noaa.gov")
        s = s.text
        radarTables = pd.read_html(s)
        radarSites = []
        for radarDf in radarTables:
            for radarList in radarDf.values.tolist():
                for radarStr in radarList:
                    if pd.isna(radarStr):
                        continue
                    icaoStr = " ".join(re.findall("[a-zA-Z]+", radarStr))
                    if icaoStr not in radarSites:
                        if icaoStr not in blackList:
                            radarSites.append(icaoStr)
                            print(icaoStr)
    else:
        radarSite = sys.argv[1]
        time = dt.utcnow().replace(tzinfo=pytz.UTC)
        conn = NexradAwsInterface()
        try:        
            radar = getRadarData(conn, radarSite, time)
        except TypeError:
            print(radarSite, "is offline")
