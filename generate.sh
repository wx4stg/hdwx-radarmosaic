#!/bin/bash
MY_DIR=`pwd`
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
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
rm -rf radarData/
mkdir radarData/
if [ $min == 0 ]
then
    declare -a targetDirs=("./output/products/radar/local" "./output/products/radar/regional" "./output/products/radar/national" "./output/gisproducts/radar/local" "./output/gisproducts/radar/regional" "./output/gisproducts/radar/national")
else
    declare -a targetDirs=("./output/products/radar/local" "./output/products/radar/regional" "./output/gisproducts/radar/local" "./output/gisproducts/radar/regional")
fi
for targetDir in "${targetDirs[@]}"
do
    mkdir -p $targetDir
    cd $targetDir
    rm *0*
    for file in *
    do 
        name=${file#*}
        prefix=${name%.*}
        idx=${prefix##*[[:alpha:]]}
        prefix=${prefix%%[0-9]*}
        suffix=${name##*.}
        mv -i "$file" "${prefix}""$(printf '%d' $((10#$idx-1)))"."${suffix}"
    done
    cd ../../../../
done
radarStr=`~/miniconda3/envs/HDWX/bin/python3 fetchRadar.py`
radars=($radarStr)
i=0
echo "Fetching data..."
for radar in $radarStr
do
    ~/miniconda3/envs/HDWX/bin/python3 fetchRadar.py $radar & >> /dev/null
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
if [ $min == 0 ]
then
    echo "Plotting national mosaic"
    ~/miniconda3/envs/HDWX/bin/python3 mosaic.py national $minToPass &
    pypids[0]=$!
fi
echo "Plotting regional mosaic"
~/miniconda3/envs/HDWX/bin/python3 mosaic.py regional $minToPass &
pypids[1]=$!
echo "Plotting local mosaic"
~/miniconda3/envs/HDWX/bin/python3 mosaic.py local $minToPass &
pypids[2]=$!
for pypid in ${pypids[*]}
do
    wait $pypid
done
cd $MY_DIR
