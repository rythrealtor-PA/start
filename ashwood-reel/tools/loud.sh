#!/bin/sh
# two-pass loudnorm: loud.sh in.wav out.wav I TP
in=$1; out=$2; I=$3; TP=$4
j=$(ffmpeg -hide_banner -i "$in" -af loudnorm=I=$I:TP=$TP:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$j" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }
ffmpeg -v error -y -i "$in" -af "loudnorm=I=$I:TP=$TP:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -c:a pcm_s24le "$out"
ffmpeg -hide_banner -i "$out" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tr -s ' ' | tr '\n' ' '; echo " <- $out"
