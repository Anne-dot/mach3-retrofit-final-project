import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor

loader = DxfLoader()
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_file_path = os.path.join(test_data_dir, "DXF", "complex_case.dxf")

# Load the DXF file
success, doc, message = loader.load_dxf(dxf_file_path)

# Check if loading was successful
if success:
    print(f"{message}")
    
    # Directly check entities
    modelspace = doc.modelspace()
    print("\nDIRECT ENTITY CHECK:")
    for entity in modelspace:
        if entity.dxftype() == "CIRCLE" and "EDGE.DRILL" in entity.dxf.layer:
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
else:
    print(f"{message}")

# Now run regular extraction
extractor = DrillingExtractor()
success, drilling_info, message = extractor.extract_all_drilling_info(doc)

if success:
    print(f"\n{message}")
    
    # Print all vertical drilling points
    print("\nVertical Drilling Points:")
    for i, point in enumerate(drilling_info['parameters']['vertical']):
        print(f"{i+1}. Position: {point['position']}, Diameter: {point['diameter']}mm, Depth: {point['depth']}mm")
    
    # Print all horizontal drilling points
    print("\nHorizontal Drilling Points:")
    for i, point in enumerate(drilling_info['parameters']['horizontal']):
        print(f"{i+1}. Position: {point['position']}, Diameter: {point['diameter']}mm, Depth: {point['depth']}mm, Edge: {point['edge']}")
else:
    print(f"{message}")