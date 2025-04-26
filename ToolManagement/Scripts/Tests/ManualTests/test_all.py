import os
import pandas as pd

# Create directories
os.makedirs(r"C:\Mach3\ToolManagement\Logs", exist_ok=True)
os.makedirs(r"C:\Mach3\ToolManagement\Data", exist_ok=True)

# Test CSV handling
df = pd.DataFrame({
	'tool_number': [1, 2, 3],
	'tool_type': ['Mill', 'Drill', 'Saw'],
	'diameter': [6.0, 8.0, 10.0]
})
df.to_csv(r"C:\Mach3\ToolManagement\Data\test_tools.csv", index=False)

# Write log
with open(r"C:\Mach3\ToolManagement\Logs\test_log.txt", "w") as f:
	f.write("Test completed successfully\n")

print("All tests passed!")
