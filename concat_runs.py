import os
import yaml
import csv
import sys

def display_help():
    print("Usage: python script.py <base_directory>")
    print("This script processes benchmark data from the specified base directory.")
    print("If no base directory is provided, this help message will be displayed.")

def main(base_directory):
    # Load config.yaml file
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    BASE_HEADERS = ['id', 'timestamp', 'name', 'vram', 'power limit']
    # Create a dictionary to store the benchmark data
    benchmark_data = {benchmark: {'headers': BASE_HEADERS.copy(), 'rows': []} for benchmark in config['benchmarks']}

    # Iterate through the subdirectories in the base directory
    for subdir in os.listdir(base_directory):
        subdir_path = os.path.join(base_directory, subdir)
        if os.path.isdir(subdir_path):
            # Extract the device name from the subdir name
            splits = subdir.split(':')
            device_name = splits[0]
            vram = splits[1]
            power_limit = splits[2]
            time = splits[-1]

            for benchmark_name in config['benchmarks']:
                csv_file = os.path.join(subdir_path, f"{benchmark_name}.csv")

                if os.path.exists(csv_file):
                    with open(csv_file, 'r') as f:
                        reader = csv.reader(f)
                        headers = next(reader)  # Get the header row
                        if BASE_HEADERS == benchmark_data[benchmark_name]['headers']:  # Only device header initially
                            benchmark_data[benchmark_name]['headers'].extend(headers)
                        rows = [row for row in reader]

                    # Append device name to each row and add to benchmark data
                    for row in rows:
                        benchmark_data[benchmark_name]['rows'].append([subdir, time, device_name, vram, power_limit] + row)
                else:
                    print(f"File {csv_file} not found for run {subdir}")

    # Create a master CSV file for each benchmark
    for benchmark_name, data in benchmark_data.items():
        with open(f"{base_directory}/{benchmark_name}_master.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data['headers'])  # Write the header row
            writer.writerows(data['rows'])  # Write the data rows

if __name__ == "__main__":
    if len(sys.argv) < 2:
        display_help()
        sys.exit(1)
    
    base_directory = sys.argv[1]
    if not os.path.isdir(base_directory):
        print(f"Error: '{base_directory}' is not a valid directory.")
        display_help()
        sys.exit(1)
    
    main(base_directory)