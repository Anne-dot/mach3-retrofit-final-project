"""
Test script to verify ezdxf library can read and parse DXF files.
Demonstrates basic DXF loading functionality and extracts key information.

This script will:
1. Load a DXF test file using ezdxf
2. Print summary information about the file
3. Extract and display layer names
4. Extract and display entity counts by type
5. Stay open at the end on Windows by waiting for input

Places this in Scripts/Tests/UnitTests/
"""
import os
import sys
import platform

# Add parent directory to path so Python can find packages
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import ezdxf
    print(f"Successfully imported ezdxf version {ezdxf.__version__}")
except ImportError as e:
    print(f"Error importing ezdxf: {e}")
    print("Please install ezdxf with: pip install ezdxf")
    if platform.system() == "Windows":
        input("Press Enter to exit...")
    sys.exit(1)

def test_dxf_loading():
    """Test loading a DXF file with ezdxf."""
    # Construct path to test files directory using platform-independent methods
    test_data_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'TestData', 
        'DXF'
    ))
    
    # Find the first DXF file in the directory
    dxf_files = [f for f in os.listdir(test_data_dir) if f.lower().endswith('.dxf')]
    
    if not dxf_files:
        print(f"No DXF files found in {test_data_dir}")
        return False
        
    test_file = os.path.join(test_data_dir, dxf_files[0])
    print(f"Testing with file: {test_file}")
    
    try:
        # Load the DXF file
        doc = ezdxf.readfile(test_file)
        
        # Basic file information
        print("\nDXF Version:", doc.dxfversion)
        print("Header Variables:", len(doc.header))
        
        # Extract layers
        print("\nLayers in file:")
        for layer in doc.layers:
            print(f"  - {layer.dxf.name}")
        
        # Count entities by type
        modelspace = doc.modelspace()
        entity_counts = {}
        
        for entity in modelspace:
            entity_type = entity.dxftype()
            if entity_type not in entity_counts:
                entity_counts[entity_type] = 0
            entity_counts[entity_type] += 1
        
        print("\nEntity counts:")
        for entity_type, count in entity_counts.items():
            print(f"  - {entity_type}: {count}")
            
        # Display information about specific entities
        if 'CIRCLE' in entity_counts and entity_counts['CIRCLE'] > 0:
            print("\nSample CIRCLE entity information:")
            for entity in modelspace:
                if entity.dxftype() == 'CIRCLE':
                    print(f"  - Layer: {entity.dxf.layer}")
                    print(f"  - Center: ({entity.dxf.center.x}, {entity.dxf.center.y})")
                    print(f"  - Radius: {entity.dxf.radius}")
                    break
        
        print("\nDXF file successfully loaded and parsed!")
        return True
        
    except ezdxf.DXFError as e:
        print(f"Error reading DXF file: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print(f"Python version: {platform.python_version()}")
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    success = test_dxf_loading()
    
    print("\nTest result:", "SUCCESS" if success else "FAILURE")
    
    # Keep console window open on Windows
    if platform.system() == "Windows":
        print("\nPress Enter to exit...")
        input()
