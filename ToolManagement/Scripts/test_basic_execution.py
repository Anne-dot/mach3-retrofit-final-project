import sys
import os
import datetime

# Create log directory if it doesn't exist
log_dir = r"C:\Mach3\ToolManagement\Logs"
os.makedirs(log_dir, exist_ok=True)

# Log execution
log_file = os.path.join(log_dir, "python_test_log.txt")
with open(log_file, "a") as f:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"{timestamp} - Basic execution test ran successfully\n")

# Create status file for Mach3 to detect
status_file = os.path.join(log_dir, "execution_status.txt")
with open(status_file, "w") as f:
    f.write("SUCCESS")

print("Basic execution test completed successfully")
sys.exit(0)  # Exit with success code
