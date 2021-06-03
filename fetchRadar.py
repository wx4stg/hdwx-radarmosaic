#!/usr/bin/env python3
import sys

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def getRadarData(connex, site):
    import pytz
    currentTime = dt.utcnow().replace(tzinfo=pytz.UTC)
    allScans = connex.get_avail_scans(currentTime.year, currentTime.month, currentTime.day, site)
    if allScans[-1].scan_time > currentTime - timedelta(minutes=20):
        connex.download(allScans[-1], path.join(getcwd(), "radarData"))
        warningString = str(dt.utcnow())+" "+site+" used amazon backup\n"
        logFile = open("warnings.log", "a")
        logFile.write(warningString)
        logFile.close()
    else:
        allScanTimes = [scan.scan_time for scan in allScans]
        for scanTime in sorted(allScanTimes):
            print(scanTime)
        warningString = str(dt.utcnow())+" "+site+" has not published data in the past 20 minutes\n"
        logFile = open("warnings.log", "a")
        logFile.write(warningString)
        logFile.close()
        print("\n\n\n\n\n")
    


def amazonBackup(radarSite):
    from nexradaws import NexradAwsInterface
    try:
        conn = NexradAwsInterface()
        getRadarData(conn, radarSite)
    except TypeError:
        warningString = str(dt.utcnow())+" exception occurred when fetching "+radarSite+", skipping...\n"
        logFile = open("warnings.log", "a")
        logFile.write(warningString)
        logFile.close()
    


if __name__ == "__main__":
    blackList = ["TJUA", "PABC", "PACG", "PAEC", "PAHG", "PAIH", "PAKC", "PAPD", "PGUA", "PHKI", "PHKM", "PHMO", "PHWA", "RKJK", "RKSG", "RODN"]
    if len(sys.argv) == 1:
        import re
        import pandas as pd
        import requests
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
        from datetime import datetime as dt
        from os import getcwd, path, listdir
        from datetime import timedelta
        radarSite = sys.argv[1]
        radarDir = path.join("/coriolis-ldm/gempak/nexrad/NIDS/", radarSite[1:])
        radarDir = path.join(radarDir, "N0Q")
        try:
            coriolisFiles = sorted(listdir(radarDir))
            lastScanFile = coriolisFiles[-1]
            lastScanTime = lastScanFile[-11:]
            lastScanTime = dt.strptime(lastScanTime, "%y%m%d_%H%M")
            if lastScanTime > dt.utcnow() - timedelta(minutes=10):
                import shutil
                radarSrcPath = path.join(radarDir, lastScanFile)
                shutil.copy(radarSrcPath, "radarData/")
            else:
                amazonBackup(radarSite)
        except:
            amazonBackup(radarSite)