#!/bin/bash
MY_DIR=`pwd`
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
min=`date +"%M"`
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
radarStr=`python3 fetchRadar.py`
radars=($radarStr)
i=0
echo "Fetching data..."
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
if [ $min == 0 ]
then
    echo "Plotting national mosaic"
    python3 mosaic.py national $min &
    pypids[0]=$!
fi
echo "Plotting regional mosaic"
python3 mosaic.py regional $min &
pypids[1]=$!
echo "Plotting local mosaic"
python3 mosaic.py local $min &
pypids[2]=$!
for pypid in ${pypids[*]}
do
    wait $pypid
done
cd $MY_DIR
