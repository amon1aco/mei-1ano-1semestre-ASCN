import sys
import csv
from prettytable import PrettyTable

def analyze_results(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        response_times = []
        start_times = []
        end_times = []

        for row in reader:
            response_times.append(float(row['elapsed']))
            start_times.append(float(row['timeStamp']))
            end_times.append(float(row['timeStamp']) + float(row['elapsed']))

        avg_response_time = sum(response_times) / len(response_times)
        throughput = len(response_times) / ((max(end_times) - min(start_times)) / 1000)

        table = PrettyTable()
        table.field_names = ["Metric", "Value"]
        table.add_row(["Average Response Time (ms)", round(avg_response_time, 2)])
        table.add_row(["Throughput (requests/sec)", round(throughput, 2)])
        
        return table

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 process_results.py <results_file>")
        sys.exit(1)

    results_file = sys.argv[1]
    result_table = analyze_results(results_file)
    print(result_table)
