import os
import yaml
import csv

# Load config.yaml file
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create a dictionary to store the benchmark data
benchmark_data = {benchmark: {'headers': ['id', 'name', 'power limit'], 'rows': []} for benchmark in config['benchmarks']}

# Set the top-level directory to search through
top_level_dir = 'runs'

# Iterate through the subdirectories in the top-level directory
for subdir in os.listdir(top_level_dir):
    subdir_path = os.path.join(top_level_dir, subdir)
    if os.path.isdir(subdir_path):
        # Extract the device name from the subdir name
        device_name = subdir.split(':')[0]

        for benchmark_name in config['benchmarks']:
            csv_file = os.path.join(subdir_path, f"{benchmark_name}.csv")

            if os.path.exists(csv_file):
                with open(csv_file, 'r') as f:
                    reader = csv.reader(f)
                    headers = next(reader)  # Get the header row
                    if len(benchmark_data[benchmark_name]['headers']) == 1:  # Only device header initially
                        benchmark_data[benchmark_name]['headers'].extend(headers)
                    rows = [row for row in reader]

                # Append device name to each row and add to benchmark data
                for row in rows:
                    benchmark_data[benchmark_name]['rows'].append([subdir, ] + row)
            else:
                print(f"File {csv_file} not found for run {subdir}")

# Create a master CSV file for each benchmark
for benchmark_name, data in benchmark_data.items():
    with open(f"runs/{benchmark_name}_master.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data['headers'])  # Write the header row
        writer.writerows(data['rows'])  # Write the data rows