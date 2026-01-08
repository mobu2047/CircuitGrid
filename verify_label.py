
import sys
import os
sys.path.append(r"c:\Users\tiany\Desktop\MAPS-master")

import numpy as np
from ppm_construction.circuit_editor.models.grid_model import GridModel, EdgeData
from ppm_construction.data_syn.grid_rules import get_latex_line_draw, LABEL_TYPE_STRING, TYPE_RESISTOR, TYPE_DIODE, TYPE_VOLTAGE_SOURCE

def verify_label_support():
    print("Verifying Label Support...")
    
    # Case Fallback: Value 0 -> Fallback to Label R0
    try:
        latex = get_latex_line_draw(0, 0, 3, 0, 
                                    type_number=TYPE_RESISTOR,
                                    label_subscript=0, 
                                    value=0, value_unit=0, use_value_annotation=True,
                                    label_subscript_type=0, note='v10') 
        print(f"Generated LaTeX (Resistor Fallback): {latex.strip()}")
        if "R_{ 0 }" in latex.replace(" ", ""):
             print("PASS: Resistor falls back to Label R0")
        elif "l=$$" in latex:
             print("FAIL: Resistor hidden (Expected fallback)")
        else:
             print(f"WARN: Check Latex: {latex}")
    except Exception as e:
        print(f"FAIL: Resistor case crashed: {e}")

    # Case Voltage: Value 0 -> Fallback to Label 'vdd'
    try:
        latex = get_latex_line_draw(0, 0, 3, 0, 
                                    type_number=TYPE_VOLTAGE_SOURCE,
                                    label_subscript="vdd",
                                    value=0, value_unit=0, use_value_annotation=True,
                                    label_subscript_type=LABEL_TYPE_STRING, note='v10')
        print(f"Generated LaTeX (Voltage Fallback): {latex.__repr__()}")
        # Voltage source uses v=...
        if "v=$vdd$" in latex.replace(" ", "") or "v=vdd" in latex:
             print("PASS: Voltage Source falls back to label 'vdd'")
        elif "vdd" in latex:
             print("PASS: Voltage Source contains 'vdd' (Format might vary)")
        else:
             print(f"FAIL: Voltage Source missing 'vdd'")
    except Exception as e:
        print(f"FAIL: Voltage Source case crashed: {e}")

    # Case Diode: Value Mode -> Show Label
    try:
        latex = get_latex_line_draw(0, 0, 3, 0, 
                                    type_number=TYPE_DIODE,
                                    label_subscript="D1",
                                    value=0, value_unit=0, use_value_annotation=True,
                                    label_subscript_type=LABEL_TYPE_STRING, note='v10')
        print(f"Generated LaTeX (Diode): {latex.strip()}")
        if "l=$D1$" in latex.replace(" ", "") or "l=D1" in latex:
             print("PASS: Diode shows label 'D1'")
        else:
             print(f"FAIL: Diode description missing D1: {latex}")

    except Exception as e:
        print(f"FAIL: Diode case crashed: {e}")

if __name__ == "__main__":
    verify_label_support()
