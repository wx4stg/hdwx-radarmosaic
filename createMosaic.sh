#!/bin/bash
export PYART_QUIET=TRUE
rm -rf radarData/
mkdir radarData/
radarStr=`python3 fetchRadar.py`
radars=($radarStr)
i=0
for radar in $radarStr
do
    python3 fetchRadar.py $radar & >> /dev/null
    pids[${i}]=$!
    ((i=i+1))
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
for pid in ${pids[*]}
do
    wait $pid
done
python3 mosaic.py
