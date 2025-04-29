import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

# Simple DXF file selector
def select_dxf_file():
    """Display a simple selection menu for DXF files."""
    dxf_files = [f for f in os.listdir(dxf_dir) if f.lower().endswith('.dxf')]
    
    if not dxf_files:
        print("No DXF files found in TestData/DXF directory.")
        return None
    
    print("\nAvailable DXF files:")
    for i, file in enumerate(dxf_files):
        print(f"{i+1}. {file}")
    
    while True:
        try:
            choice = input("\nSelect a file number (or press Enter for default): ")
            if choice.strip() == "":
                # Default to first file
                selected_index = 0
                break
            else:
                selected_index = int(choice) - 1
                if 0 <= selected_index < len(dxf_files):
                    break
                else:
                    print(f"Please enter a number between 1 and {len(dxf_files)}")
        except ValueError:
            print("Please enter a valid number")
    
    selected_file = dxf_files[selected_index]
    return os.path.join(dxf_dir, selected_file)

print("=== Drilling Point Extraction Test ===")

# Let user select a DXF file
dxf_file_path = select_dxf_file()
if not dxf_file_path:
    print("No DXF file selected. Exiting.")
    sys.exit(1)

print(f"Using test DXF file: {dxf_file_path}")

# Create loader and extractor
loader = DxfLoader()
extractor = DrillingExtractor()

# Step 1: Load the DXF file
print("\nStep 1: Loading DXF file...")
success, doc, message = loader.load_dxf(dxf_file_path)

if not success:
    print(f"Error loading DXF: {message}")
    sys.exit(1)

print(f"SUCCESS: DXF loaded successfully: {message}")

# Step 2: Direct entity check for horizontal drilling
print("\nStep 2: Performing direct entity check...")
modelspace = doc.modelspace()
found_horizontal_entities = False

print("\nDIRECT ENTITY CHECK:")
for entity in modelspace:
    if entity.dxftype() == "CIRCLE" and "EDGE.DRILL" in entity.dxf.layer:
        found_horizontal_entities = True
        print(f"Circle on layer: {entity.dxf.layer}")
        print(f"  Position: {entity.dxf.center}")
        # Try to extract extrusion direction values
        try:
            x_dir = entity.get_dxf_attrib(210, default=0.0)
            y_dir = entity.get_dxf_attrib(220, default=0.0)
            z_dir = entity.get_dxf_attrib(230, default=0.0)
            print(f"  Extrusion direction: ({x_dir}, {y_dir}, {z_dir})")
        except Exception as e:
            print(f"  Cannot extract extrusion: {str(e)}")

if not found_horizontal_entities:
    print("No horizontal drilling entities found in direct check.")

# Step 3: Extract drilling information
print("\nStep 3: Extracting drilling information...")
drill_success, drilling_info, drill_message = extractor.extract_all_drilling_info(doc)

if not drill_success:
    print(f"Error extracting drilling info: {drill_message}")
    sys.exit(1)

print(f"SUCCESS: Drilling information extracted: {drill_message}")
print(f"  Found {drilling_info['vertical_count']} vertical drilling points")
print(f"  Found {drilling_info['horizontal_count']} horizontal drilling points")

# Step 4: Display detailed drilling information
print("\nStep 4: Detailed drilling information:")

# Print all vertical drilling points
print("\nVertical Drilling Points:")
if drilling_info['parameters']['vertical']:
    for i, point in enumerate(drilling_info['parameters']['vertical']):
        print(f"{i+1}. Position: {point['position']}, Diameter: {point['diameter']}mm, Depth: {point['depth']}mm")
else:
    print("No vertical drilling points found.")

# Print all horizontal drilling points
print("\nHorizontal Drilling Points:")
if drilling_info['parameters']['horizontal']:
    for i, point in enumerate(drilling_info['parameters']['horizontal']):
        print(f"{i+1}. Position: {point['position']}, Diameter: {point['diameter']}mm, Depth: {point['depth']}mm, Edge: {point['edge']}")
else:
    print("No horizontal drilling points found.")

print("\nTest completed successfully.")