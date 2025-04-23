import subprocess

def is_tool_data_open():
    # Window title check
    name_variants = ["tool-data", "*tool-data"]

    try:
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-Process | Where-Object {$_.MainWindowTitle -and ($_.ProcessName -eq "notepad" -or $_.ProcessName -eq "wordpad")} | Select-Object -ExpandProperty MainWindowTitle'],
            capture_output=True, text=True
        )

        titles = result.stdout.lower().splitlines()
        for title in titles:
            for name in name_variants:
                if name.lower() in title:
                    print("File is open.")
                    return True

        print("File is not open.")
        return False

    except Exception as e:
        print(f"Error checking windows: {e}")
        return False

# Example use
if __name__ == "__main__":
    is_tool_data_open()

