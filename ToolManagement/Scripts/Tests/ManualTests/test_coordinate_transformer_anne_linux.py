import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor
from DXF.coordinate_transformer import WorkpieceTransformer, HorizontalDrillTransformer

loader = DxfLoader()
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_file_path = os.path.join(test_data_dir, "DXF", "complex_case.dxf")
# Load the DXF file
success, doc, message = loader.load_dxf(dxf_file_path)

# After loading the DXF file
if success:
    print(f"Successfully loaded DXF file: {os.path.basename(dxf_file_path)}")
    
    # Continue with workpiece extraction
    from DXF.workpiece_extractor import WorkpieceExtractor
    workpiece_extractor = WorkpieceExtractor()
    
    # Get workpiece information
    success_wp, workpiece_info, wp_message = workpiece_extractor.extract_workpiece_info(doc)
    
    if success_wp:
        print(f"Successfully extracted workpiece information")
        # Print key workpiece dimensions
        if 'dimensions' in workpiece_info:
            dims = workpiece_info['dimensions']
            print(f"  Width: {dims.get('width', 'N/A')}mm")
            print(f"  Height: {dims.get('height', 'N/A')}mm")
            print(f"  Thickness: {dims.get('depth', 'N/A')}mm")
            print(f"  Min X: {dims.get('min_x', 'N/A')}, Min Y: {dims.get('min_y', 'N/A')}")
            print(f"  Max X: {dims.get('max_x', 'N/A')}, Max Y: {dims.get('max_y', 'N/A')}")
        
        if 'orientation' in workpiece_info:
            orient = workpiece_info['orientation']
            print(f"  Origin aligned: {orient.get('origin_aligned', 'N/A')}")
            print(f"  Axis aligned: {orient.get('axis_aligned', 'N/A')}")
            
        # Continue with drilling extraction
        drilling_extractor = DrillingExtractor()
        
        # Get drilling information
        success_drill, drilling_info, drill_message = drilling_extractor.extract_all_drilling_info(doc)
        
        if success_drill:
            print(f"Successfully extracted drilling information")
            # print("\nDrilling info dictionary keys:")
            # for key in drilling_info:
            #     print(f"  {key}")
                                     
                            
            # Initialize coordinate transformer
            # Changed from CoordinateTransformer to WorkpieceTransformer
            workpiece_transformer = WorkpieceTransformer()
            workpiece_transformer.set_from_workpiece_info(workpiece_info)
            
            # Show the original workpiece boundary values
            print("\nOriginal workpiece boundary values:")
            print(f"  Min X: {workpiece_transformer.min_x}, Min Y: {workpiece_transformer.min_y}")
            print(f"  Max X: {workpiece_transformer.max_x}, Max Y: {workpiece_transformer.max_y}")
            
            # Transform the workpiece - note the signature may have changed
            # The updated transform_workpiece might not take rotation/mirror parameters
            success_transform, transformed_workpiece, transform_details = workpiece_transformer.transform_workpiece(
                workpiece_info
            )

            # Show transformed workpiece boundary values
            print("\nTransformed workpiece boundary values:")
            if success_transform and 'dimensions' in transformed_workpiece:
                dims = transformed_workpiece['dimensions']
                print(f"  Min X: {dims.get('min_x', 'N/A')}, Min Y: {dims.get('min_y', 'N/A')}")
                print(f"  Max X: {dims.get('max_x', 'N/A')}, Max Y: {dims.get('max_y', 'N/A')}")
            else:
                print(f"  Transform failed: {transform_details.get('message', 'Unknown error')}")
                    
            horizontal_points = drilling_info["points"]['horizontal']
                            
            print("\nHorizontal drill points (transformed in test according to doc)")
            for i, point in enumerate(horizontal_points):
                # Get original coordinates
                x, y, z = point.position
                # Determine which edge based on Z value
                edge = "front" if abs(z) < 1.0 else "back"
                # Apply corrected transformation formulas
                transformed_x = workpiece_info['dimensions']['width'] - abs(x)
                transformed_y = -workpiece_info['dimensions']['height'] if edge == "front" else 0.0
                transformed_z = workpiece_info['dimensions']['depth'] - abs(y)
                # Round to 0.1mm
                transformed_x = round(transformed_x, 1)
                transformed_y = round(transformed_y, 1)
                transformed_z = round(transformed_z, 1)
                print(f"  H{i+1}: Original: ({x}, {y}, {z}) {edge} → Expected: ({transformed_x}, {transformed_y}, {transformed_z})")
                
                # Now use the transformer to get actual results
                horizontal_transformer = HorizontalDrillTransformer()
                horizontal_transformer.set_from_workpiece_info(workpiece_info)
                success, actual_point, details = horizontal_transformer.transform_point(point.position)
                
                if success:
                    print(f"     → Actual: {actual_point} [{details.get('edge', 'unknown')}]")
                    # Check if transformation matches expectations
                    if (transformed_x, transformed_y, transformed_z) == actual_point:
                        print(f"     ✓ MATCH")
                    else:
                        print(f"     ✗ MISMATCH")
                else:
                    print(f"     ✗ Transformation failed: {details.get('message', 'Unknown error')}")
                print()
        else:
            print(f"Failed to extract drilling information: {drill_message}")
            input("Press Enter to exit...")
            sys.exit(1)
             
    else:
        print(f"Failed to extract workpiece information: {wp_message}")
        input("Press Enter to exit...")
        sys.exit(1)
else:
    print(f"Failed to load DXF file: {message}")
    input("Press Enter to exit...")
    sys.exit(1)