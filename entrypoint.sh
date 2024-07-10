#!/bin/bash

# Start a new tmux session named "bench"
tmux new-session -d -s bench

# Split the window vertically
tmux split-window -h

# In the right pane, change to the ComfyUI directory and run main.py
tmux send-keys -t bench:0.1 'cd /app/ComfyUI && python3 main.py' C-m

# Select the left pane
tmux select-pane -t bench:0.0

# Attach to the tmux session
tmux attach-session -t bench