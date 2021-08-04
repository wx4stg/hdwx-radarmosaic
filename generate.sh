#!/bin/bash
# cache original directory to allow for clean exit
MY_DIR=`pwd`
# Get and change to the containing dir
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
# Get current time minutes for the "Valid" label. Round to nearest 5 for cleanliness
min=`date +"%M"`
(( minToPass=5*((min)/5) ))
min=$(($min%10))
if [ "$min" -le "5" ]
then
    min=0
else
    min=5
fi
export PYART_QUIET=TRUE
# Delete and re-create directory for raw reflectivity data
rm -rf radarData/
mkdir radarData/
# Determine if we want a national mosaic (every 10min) or just a local/regional (every 5 min)
if [ $min == 0 ]
then
    declare -a targetDirs=("./output/products/radar/local" "./output/products/radar/regional" "./output/products/radar/national" "./output/gisproducts/radar/local" "./output/gisproducts/radar/regional" "./output/gisproducts/radar/national")
else
    declare -a targetDirs=("./output/products/radar/local" "./output/products/radar/regional" "./output/gisproducts/radar/local" "./output/gisproducts/radar/regional")
fi
# In output directory, delete frame0.png, rename frame1.png -> frame0.png, rename frame2.png -> frame1.png, etc...
for targetDir in "${targetDirs[@]}"
do
# Create target dir if it doesn't already exist
    mkdir -p $targetDir
# Change to target dir
    cd $targetDir
# Delete frame0.png
    rm *0*
# Black magic I stole from stackoverflow... /shrug
    for file in *
    do 
        name=${file#*}
        prefix=${name%.*}
        idx=${prefix##*[[:alpha:]]}
        prefix=${prefix%%[0-9]*}
        suffix=${name##*.}
        mv -i "$file" "${prefix}""$(printf '%d' $((10#$idx-1)))"."${suffix}"
    done
# Return to the original directory
    cd ../../../../
done
# Get a list of every radar we want to pull data from
radarStr=`~/miniconda3/envs/HDWX/bin/python3 fetchRadar.py`
radars=($radarStr)
i=0
echo "Fetching data..."
# I was particularly proud of how clever this was... 50 workers at a time pulling radar data
for radar in $radarStr
do
# invoke the fetchRadar script on every radar
    ~/miniconda3/envs/HDWX/bin/python3 fetchRadar.py $radar & >> /dev/null
# Capture the PID of the fetchRadar proc and store it in an array
    pids[${i}]=$!
# incriment i before next iteration
    ((i=i+1))
# I only want 50 workers, so if there are 50 active procs, wait on one to exit before starting a new one
    while [ ${#pids[@]} == 50 ]
    do
        for pid in ${pids[*]}
        do
            if ! kill -0 $pid 2>/dev/null
            then 
                pids=(${pids[@]/$pid})
            fi
        done
    done
done
# wait for the last 10 procs to exit
for pid in ${pids[*]}
do
    wait $pid
done
# Plot regional and local mosaics
echo "Plotting regional mosaic"
~/miniconda3/envs/HDWX/bin/python3 mosaic.py regional $minToPass &
pypids[0]=$!
echo "Plotting local mosaic"
~/miniconda3/envs/HDWX/bin/python3 mosaic.py local $minToPass &
pypids[1]=$!
# Plot national mosaic, if we want that
if [ $min == 0 ]
then
    echo "Plotting national mosaic"
    ~/miniconda3/envs/HDWX/bin/python3 mosaic.py national $minToPass &
    pypids[2]=$!
fi
# Wait on those to exit
for pypid in ${pypids[*]}
do
    wait $pypid
done
# go back to where we started
cd $MY_DIR
