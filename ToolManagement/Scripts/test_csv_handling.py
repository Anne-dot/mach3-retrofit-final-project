import sys
import os
import datetime
import pandas as pd

# Paths
data_dir = r"C:\Mach3\ToolManagement\Data"
log_dir = r"C:\Mach3\ToolManagement\Logs"
os.makedirs(data_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# Create test CSV
try:
    # Test data for tool properties
    test_data = {
        'tool_number': [1, 2, 3],
        'tool_type': ['Mill', 'HorizontalDrill', 'VerticalDrill'],
        'tool_direction': [6, 3, 5],
        'diameter': [6.0, 8.0, 10.0],
        'tool_length': [50.0, 75.0, 100.0]
    }
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(test_data)
    test_csv = os.path.join(data_dir, "test_tools.csv")
    df.to_csv(test_csv, index=False)
    
    # Read back and verify
    df_read = pd.read_csv(test_csv)
    
    if len(df_read) == 3 and all(df_read.columns == df.columns):
        status = "SUCCESS"
        message = "CSV handling test completed successfully"
    else:
        status = "FAILED"
        message = "CSV data verification failed"
        
except Exception as e:
    status = "ERROR"
    message = f"Exception occurred: {str(e)}"

# Log result
log_file = os.path.join(log_dir, "python_test_log.txt")
with open(log_file, "a") as f:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"{timestamp} - CSV test - {status}: {message}\n")

# Create status file for Mach3 to detect
status_file = os.path.join(log_dir, "execution_status.txt")
with open(status_file, "w") as f:
    f.write(status)

print(message)
sys.exit(0 if status == "SUCCESS" else 1)
