#!/bin/sh
# extract 60 fps full-res frames for the used source ranges: frames/<clip>/<n>.jpg, n = round(t*60)
set -e
ex() { clip=$1; a=$2; b=$3; mkdir -p frames/$clip
  n0=$(python3 -c "print(round($a*60))"); n1=$(python3 -c "print(round($b*60))")
  ss=$(python3 -c "print($n0/60)"); cnt=$((n1-n0+1))
  ffmpeg -v error -y -ss $ss -i src/$clip.mp4 -vf "fps=60:start_time=0,format=yuvj444p" -frames:v $cnt -q:v 2 -start_number $n0 frames/$clip/%05d.jpg
  echo "$clip $a-$b -> $cnt frames"; }
ex rec1 0.0 7.75
ex rec1 19.3 34.5
ex rec1 36.6 39.95
ex rec1 40.65 44.45
ex rec2 0.0 11.7
ex rec3 0.0 3.2
ex rec3 6.9 8.68
du -sh frames
