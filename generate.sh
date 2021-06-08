#!/bin/bash
export PYART_QUIET=TRUE
rm -rf radarData/
mkdir radarData/
declare -a targetDirs=("./output/products/radar/local" "./output/products/radar/regional" "./output/products/radar/national" "./output/gisproducts/radar/local" "./output/gisproducts/radar/regional" "./output/gisproducts/radar/national")
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
if [ "$1" == "--include-national" ]
then
    echo "Plotting national mosaic"
    python3 mosaic.py national
fi
echo "Plotting regional mosaic"
python3 mosaic.py regional
echo "Plotting local mosaic"
python3 mosaic.py local
if [ "$1" == "--publish" ] || [ "$2" == "--publish" ]
then
    echo "Sending to public-facing directory..."
    rsync -r output/ /var/www/html/wx4stg/.
fi