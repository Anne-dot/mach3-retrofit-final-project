import sys
import os
import datetime
import json

# Paths
data_dir = r"C:\Mach3\ToolManagement\Data"
log_dir = r"C:\Mach3\ToolManagement\Logs"
os.makedirs(data_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# Test data
test_data = {
    "test_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "test_values": [1, 2, 3, 4, 5],
    "test_status": "running"
}

# Write test file
try:
    test_file = os.path.join(data_dir, "test_data.json")
    with open(test_file, "w") as f:
        json.dump(test_data, f, indent=2)
    
    # Read test file back
    with open(test_file, "r") as f:
        read_data = json.load(f)
    
    # Verify data integrity
    if read_data["test_values"] == test_data["test_values"]:
        status = "SUCCESS"
        message = "File I/O test completed successfully"
    else:
        status = "FAILED"
        message = "Data integrity check failed"
    
except Exception as e:
    status = "ERROR"
    message = f"Exception occurred: {str(e)}"

# Log result
log_file = os.path.join(log_dir, "python_test_log.txt")
with open(log_file, "a") as f:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"{timestamp} - File I/O test - {status}: {message}\n")

# Create status file for Mach3 to detect
status_file = os.path.join(log_dir, "execution_status.txt")
with open(status_file, "w") as f:
    f.write(status)

print(message)
sys.exit(0 if status == "SUCCESS" else 1)
