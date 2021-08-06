#!/bin/bash
export PYART_QUIET=TRUE
# Get current time minutes for the "Valid" label and API data. Round to nearest 5 for cleanliness...
# I can't make a mosaic at exactly every 5th minute, as not all of the data from radars will have been pushed
# to coriolis or aws. So the 00:00 mosaic may contain radar data gathered at 00:01 (if that particular radar site has a fast enough uplink)
# and may not contain the data from all sites gathered before 00:00 (if their link is unusually slow)
# This is obviously an imperfect solution, but it was the best I could think of...
min=`date +"%M"`
(( minToPass=5*((min)/5) ))
# Delete and re-create directory for raw reflectivity data
rm -rf radarData/
mkdir radarData/
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
# wait for the last 50 procs to exit
for pid in ${pids[*]}
do
    wait $pid
done
# Plot mosaics
echo "Plotting regional mosaic"
~/miniconda3/envs/HDWX/bin/python3 mosaic.py regional $minToPass &
pypids[0]=$!
echo "Plotting local mosaic"
~/miniconda3/envs/HDWX/bin/python3 mosaic.py local $minToPass &
pypids[1]=$!
echo "Plotting national mosaic"
~/miniconda3/envs/HDWX/bin/python3 mosaic.py national $minToPass &
pypids[2]=$!
# Wait on those to exit
for pypid in ${pypids[*]}
do
    wait $pypid
done
# metadata handling script
~/miniconda3/envs/HDWX/bin/python3 jsonManager.py 