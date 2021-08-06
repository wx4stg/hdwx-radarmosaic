#!/usr/bin/env python3
# JSON/Metadata pre-push script for python-based HDWX
# Created 4 August 2021 by Sam Gardner <stgardner4@tamu.edu>

import json
from os import path, listdir, walk, remove
from datetime import datetime as dt
import shutil
from pathlib import Path
from natsort import natsorted

if __name__ == "__main__":
    tmpFrameMetaStorage = path.join(path.dirname(path.abspath(__file__)), "frameMetaData/")
    outputDir = path.join(path.dirname(path.abspath(__file__)), "output/")
    metadataOutDir = path.join(outputDir, "metadata/")
    publishTime = dt.utcnow()
    for hour in listdir(tmpFrameMetaStorage):
        metadataForHour = path.join(tmpFrameMetaStorage, hour)
        if int(hour) == publishTime.hour:
            currentRunDir = path.join(tmpFrameMetaStorage, str(hour))
            for productID in sorted(listdir(metadataForHour)):
                framesArray = list()
                productFramesJsonPath = path.join(metadataForHour, productID)
                for frameJsonFilename in natsorted(listdir(productFramesJsonPath)):
                    frameJsonPath = path.join(productFramesJsonPath, frameJsonFilename)
                    with open(frameJsonPath) as readJson:
                        frameJson = json.load(readJson)
                        framesArray.append(frameJson)
                productRunDict = {
                    "publishTime" : int(dt.utcnow().strftime("%Y%m%d%H%M")),
                    "pathExtension" : publishTime.strftime("%Y/%m/%d/%H00/"),
                    "runName" : publishTime.strftime("%d %b %Y %HZ"),
                    "availableFrameCount" : len(framesArray),
                    "totalFrameCount" : 12,
                    "productFrames" : framesArray
                }
                Path(saveFilePath).mkdir(parents=True, exist_ok=True)
                saveFilePath = path.join(path.join(metadataOutDir, "products/"), productID)
                for oldMetaData in listdir(saveFilePath):
                    remove(path.join(saveFilePath, oldMetaData))
                saveFilePath = path.join(saveFilePath, publishTime.strftime("%Y%m%d%H00")+".json")
                with open(saveFilePath, "w") as jsonWrite:
                    json.dump(productRunDict, jsonWrite, indent=4)
        else:
            shutil.rmtree(metadataForHour)
    for tree in walk(outputDir):
        if tree[1] == [] and "metadata" not in tree[0]:
            if publishTime.strftime("%Y/%m/%d/%H00") not in tree[0]:
                shutil.rmtree(tree[0])
            

