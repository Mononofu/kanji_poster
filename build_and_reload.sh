#!/bin/sh

python3 -m http.server --directory html &
SERVER_PID=$!
trap 'kill $SERVER_PID' EXIT INT TERM

watchexec -e py -r "python3 generate_tex.py --minimal --colormap Oslo"