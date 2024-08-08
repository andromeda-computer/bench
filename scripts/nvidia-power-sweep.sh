#!/bin/bash

# Default values
power_limit=185
max_limit=350
increment=5

# Function to show help message
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -start <power>       Starting power limit (default: 185)"
    echo "  -end <max_power>     Maximum power limit (default: 350)"
    echo "  -increment <value>   Increment value (default: 5)"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -start)
            power_limit="$2"
            shift # past argument
            shift # past value
            ;;
        -end)
            max_limit="$2"
            shift # past argument
            shift # past value
            ;;
        -increment)
            increment="$2"
            shift # past argument
            shift # past value
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            show_help >&2   # Redirect help message to stderr.
            exit 1          # Exit with error status code.
    esac 
done

# Check if required parameters are set correctly; adjust conditions based on your needs.
if [[ -z "$power_limit" || -z "$max_limit" || -z "$increment" ]]; then 
    show_help >&2   # Show help message if parameters are missing.
    exit 1          # Exit with error status code.
fi

echo "Starting power limit: $power_limit"
echo "Maximum power limit: $max_limit"
echo "Increment by: $increment"

while [ $power_limit -le $max_limit ]; do
	echo "Setting power limit to $power_limit W"
	sudo nvidia-smi -pl $power_limit

	sleep 1

    echo "Starting Comfy process..."
    
    # Start comfy main.py in the background
    (
		# TODO shouldnt need this at all
        ~/code/comfy-bench/env/bin/python ~/code/comfy-bench/main.py > /dev/null 2>&1
    ) &

    # Store the PID of the comfy process
    COMFY_PID=$!

	# Function to keep sudo alive
	keep_sudo_alive() {
		while true; do
			sudo -v
			sleep 50
		done
	}

	# Start the keep_sudo_alive function in the background
	keep_sudo_alive &
	KEEP_SUDO_PID=$!

    # Wait for 3
	sleep 3

	echo "Running Python script..."
	# TODO this is a hack
	env/bin/python ../main.py

	kill $COMFY_PID 2>/dev/null
	kill $KEEP_SUDO_PID

	# Increment power limit
	power_limit=$((power_limit + increment))

done

echo "Script completed."
