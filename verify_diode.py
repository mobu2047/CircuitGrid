
import sys
import os
sys.path.append(r"c:\Users\tiany\Desktop\MAPS-master")

from ppm_construction.data_syn.grid_rules import TYPE_DIODE, TYPE_RESISTOR, get_latex_line_draw
from ppm_construction.circuit_editor.registry.component_registry import EdgeComponentRegistry, NodeComponentRegistry
from ppm_construction.circuit_editor.views.component_renderer import ComponentRenderer

def verify_refactor():
    print("Verifying Diode Refactor...")
    
    # 1. Constants
    print(f"TYPE_DIODE = {TYPE_DIODE}")
    assert TYPE_DIODE == 11, "TYPE_DIODE should be 11"
    
    # 2. Registry
    diode_config = EdgeComponentRegistry.get(11)
    if diode_config:
        print(f"PASS: ID 11 in EdgeRegistry is {diode_config.display_name}")
    else:
        print(f"FAIL: ID 11 in EdgeRegistry is None")

    node_diode = NodeComponentRegistry.get(3)
    if not node_diode:
         print("PASS: ID 3 removed from NodeComponentRegistry")
    else:
         print(f"WARN: ID 3 in NodeRegistry is {node_diode.display_name} (Should be None or not Diode)")
         if node_diode.display_name == "Diode":
             print("FAIL: Diode still in NodeRegistry")

    # 3. Renderer
    if 11 in ComponentRenderer._edge_renderers:
        print("PASS: Renderer registered for ID 11")
    else:
        print("FAIL: No renderer for ID 11")

    # 4. LaTeX Generation
    try:
        # Simulate args for get_latex_line_draw
        # x1, y1, x2, y2, type_number, label, value, value_unit, use_value_annotation, measure_type, measure_label, measure_direction, direction, label_subscript_type, control_label, note
        
        # We need to mock components_latex_info list used inside get_latex_line_draw??? 
        # Wait, get_latex_line_draw imports specific lists?
        # It uses global variables in grid_rules?
        # Let's check grid_rules.py... lines 45-120 define components_latex_info.
        # I didn't update that list! I only updated constants!
        # OH NO. I missed `components_latex_info` in `grid_rules.py`.
        # I need to check if `components_latex_info` needs updating. 
        # It maps ID to [circuitikz_type, label, unit].
        # If I added TYPE_DIODE=11, I need to make sure `components_latex_info` has 12 elements!
        pass 
    except Exception as e:
        print(f"Verification setup error: {e}")

if __name__ == "__main__":
    verify_refactor()
