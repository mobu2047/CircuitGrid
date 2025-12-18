import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)
import json
import numpy as np
import random
import subprocess
import shutil
import copy
from abc import ABC, abstractmethod

from concurrent.futures import ThreadPoolExecutor
import threading

import argparse
from tqdm import tqdm

from grid_rules import (
    gen_circuit, Circuit,
    TYPE_RESISTOR, TYPE_CAPACITOR, TYPE_INDUCTOR, 
    TYPE_VOLTAGE_SOURCE, TYPE_CURRENT_SOURCE, 
    TYPE_VCCS, TYPE_VCVS, TYPE_CCCS, TYPE_CCVS, 
    TYPE_SHORT, MEAS_TYPE_VOLTAGE, MEAS_TYPE_CURRENT,
    unit_scales
)

# ============================================================================
# Component type names for natural language generation
# ============================================================================
COMPONENT_TYPE_NAMES = {
    TYPE_RESISTOR: ["resistor", "resistance", "resistive element"],
    TYPE_CAPACITOR: ["capacitor", "capacitance", "capacitive element"],
    TYPE_INDUCTOR: ["inductor", "inductance", "inductive element"],
    TYPE_VOLTAGE_SOURCE: ["voltage source", "voltage supply", "DC voltage source"],
    TYPE_CURRENT_SOURCE: ["current source", "current supply", "DC current source"],
    TYPE_VCCS: ["VCCS", "voltage-controlled current source"],
    TYPE_VCVS: ["VCVS", "voltage-controlled voltage source"],
    TYPE_CCCS: ["CCCS", "current-controlled current source"],
    TYPE_CCVS: ["CCVS", "current-controlled voltage source"],
}

COMPONENT_UNIT_NAMES = {
    TYPE_RESISTOR: "Ω",
    TYPE_CAPACITOR: "F",
    TYPE_INDUCTOR: "H",
    TYPE_VOLTAGE_SOURCE: "V",
    TYPE_CURRENT_SOURCE: "A",
    TYPE_VCCS: "",
    TYPE_VCVS: "",
    TYPE_CCCS: "",
    TYPE_CCVS: "",
}

UNIT_SCALE_NAMES = ["", "k", "m", "μ", "n", "p"]


# ============================================================================
# Base class for edit operations (extensible framework)
# ============================================================================
class EditOperation(ABC):
    """
    Abstract base class for circuit edit operations.
    Subclasses implement specific edit types (parameter change, topology change, etc.)
    """
    
    @abstractmethod
    def apply(self, circuit: Circuit) -> Circuit:
        """
        Apply the edit operation to a circuit.
        Returns a new modified circuit (does not modify original).
        """
        pass
    
    @abstractmethod
    def generate_instruction(self) -> str:
        """
        Generate natural language instruction describing this edit.
        """
        pass
    
    @abstractmethod
    def get_edit_type(self) -> str:
        """
        Return the type identifier for this edit operation.
        """
        pass


class ParameterEditOperation(EditOperation):
    """
    Edit operation that changes component parameter values without altering topology.
    Supports: resistors, capacitors, inductors, voltage/current sources.
    """
    
    def __init__(self, branch_index: int, old_value: float, new_value: float, 
                 old_unit: int, new_unit: int, component_type: int, component_label: str):
        """
        Args:
            branch_index: Index of the branch to modify
            old_value: Original parameter value
            new_value: New parameter value
            old_unit: Original unit scale index
            new_unit: New unit scale index (can be same as old_unit)
            component_type: Type of the component
            component_label: Label/identifier of the component
        """
        self.branch_index = branch_index
        self.old_value = old_value
        self.new_value = new_value
        self.old_unit = old_unit
        self.new_unit = new_unit
        self.component_type = component_type
        self.component_label = component_label
    
    def apply(self, circuit: Circuit) -> Circuit:
        """
        Apply parameter change to the circuit.
        Modifies the internal arrays that store component values.
        """
        # Deep copy to avoid modifying original
        new_circuit = copy.deepcopy(circuit)
        
        # Update the branch value
        if self.branch_index < len(new_circuit.branches):
            new_circuit.branches[self.branch_index]['value'] = self.new_value
            new_circuit.branches[self.branch_index]['value_unit'] = self.new_unit
        
        # Also update the underlying arrays (vcomp_value/hcomp_value)
        # This is needed for LaTeX regeneration
        # We need to find which array position corresponds to this branch
        self._update_circuit_arrays(new_circuit)
        
        return new_circuit
    
    def _update_circuit_arrays(self, circuit: Circuit):
        """
        Update the underlying component arrays based on branch modifications.
        """
        # Rebuild the arrays from branches
        add_order = 0
        for i in range(circuit.m):
            for j in range(circuit.n):
                if j < circuit.n-1 and circuit.has_hedge[i][j]:
                    if circuit.grid_nodes[i][j] != circuit.grid_nodes[i][j+1]:
                        if add_order == self.branch_index:
                            circuit.hcomp_value[i][j] = self.new_value
                            circuit.hcomp_value_unit[i][j] = self.new_unit
                            return
                        add_order += 1
                
                if i < circuit.m-1 and circuit.has_vedge[i][j]:
                    if circuit.grid_nodes[i][j] != circuit.grid_nodes[i+1][j]:
                        if add_order == self.branch_index:
                            circuit.vcomp_value[i][j] = self.new_value
                            circuit.vcomp_value_unit[i][j] = self.new_unit
                            return
                        add_order += 1
    
    def generate_instruction(self) -> str:
        """
        Generate natural language instruction with randomized phrasing.
        """
        comp_name = random.choice(COMPONENT_TYPE_NAMES.get(self.component_type, ["component"]))
        unit = COMPONENT_UNIT_NAMES.get(self.component_type, "")
        
        old_unit_prefix = UNIT_SCALE_NAMES[int(self.old_unit)]
        new_unit_prefix = UNIT_SCALE_NAMES[int(self.new_unit)]
        
        old_val_str = f"{int(self.old_value)}{old_unit_prefix}{unit}"
        new_val_str = f"{int(self.new_value)}{new_unit_prefix}{unit}"
        
        # Multiple template options for variety
        templates = [
            f"Change the {comp_name} (labeled {self.component_label}) from {old_val_str} to {new_val_str}.",
            f"Modify the value of {comp_name} {self.component_label} from {old_val_str} to {new_val_str}.",
            f"Update {comp_name} {self.component_label}: change its value from {old_val_str} to {new_val_str}.",
            f"Adjust the {comp_name} {self.component_label} parameter from {old_val_str} to {new_val_str}.",
            f"Set the {comp_name} {self.component_label} to {new_val_str} (previously {old_val_str}).",
            f"Replace the {old_val_str} {comp_name} ({self.component_label}) with a {new_val_str} one.",
        ]
        
        return random.choice(templates)
    
    def get_edit_type(self) -> str:
        return "parameter_change"


# ============================================================================
# Edit Generator - creates random edit operations
# ============================================================================
class EditGenerator:
    """
    Generates random edit operations for a circuit.
    Extensible: add new edit types by implementing new EditOperation subclasses.
    """
    
    # Supported edit types (add more as needed)
    EDIT_TYPE_PARAMETER = "parameter"
    # Future: EDIT_TYPE_ADD_COMPONENT = "add_component"
    # Future: EDIT_TYPE_REMOVE_COMPONENT = "remove_component"
    # Future: EDIT_TYPE_TOPOLOGY = "topology"
    
    def __init__(self, edit_types: list = None):
        """
        Args:
            edit_types: List of edit types to enable. Default: ["parameter"]
        """
        self.edit_types = edit_types or [self.EDIT_TYPE_PARAMETER]
    
    def generate_parameter_edit(self, circuit: Circuit) -> ParameterEditOperation:
        """
        Generate a random parameter change edit for a circuit.
        """
        # Find editable components (those with numeric values)
        editable_types = [TYPE_RESISTOR, TYPE_CAPACITOR, TYPE_INDUCTOR, 
                        TYPE_VOLTAGE_SOURCE, TYPE_CURRENT_SOURCE]
        
        editable_branches = [
            (idx, br) for idx, br in enumerate(circuit.branches) 
            if br['type'] in editable_types
        ]
        
        if not editable_branches:
            return None
        
        # Randomly select a branch to edit
        branch_idx, branch = random.choice(editable_branches)
        
        old_value = branch['value']
        old_unit = branch['value_unit']
        component_type = branch['type']
        component_label = branch.get('label', branch_idx)
        
        # Generate new value (different from old)
        # Strategy: multiply or divide by a factor, or use a completely new value
        strategies = ['multiply', 'divide', 'new_value']
        strategy = random.choice(strategies)
        
        if strategy == 'multiply':
            factor = random.choice([2, 3, 5, 10])
            new_value = old_value * factor
        elif strategy == 'divide':
            factor = random.choice([2, 5, 10])
            new_value = max(1, old_value / factor)
        else:
            # Generate a completely new random value
            new_value = random.choice([1, 2, 5, 10, 20, 50, 100, 200, 500])
            while new_value == old_value:
                new_value = random.choice([1, 2, 5, 10, 20, 50, 100, 200, 500])
        
        # Optionally change unit scale
        new_unit = old_unit
        if random.random() < 0.3:  # 30% chance to change unit
            possible_units = [0, 1]  # "" and "k"
            new_unit = random.choice(possible_units)
        
        return ParameterEditOperation(
            branch_index=branch_idx,
            old_value=old_value,
            new_value=new_value,
            old_unit=old_unit,
            new_unit=new_unit,
            component_type=component_type,
            component_label=str(int(component_label)) if isinstance(component_label, float) else str(component_label)
        )
    
    def generate_edits(self, circuit: Circuit, num_edits: int = 1) -> list:
        """
        Generate multiple edit operations for a circuit.
        
        Args:
            circuit: The base circuit
            num_edits: Number of edit variants to generate
        
        Returns:
            List of EditOperation objects
        """
        edits = []
        used_branches = set()  # Avoid editing same branch multiple times
        
        for _ in range(num_edits):
            edit_type = random.choice(self.edit_types)
            
            if edit_type == self.EDIT_TYPE_PARAMETER:
                # Try to find an edit that doesn't duplicate
                for attempt in range(10):
                    edit = self.generate_parameter_edit(circuit)
                    if edit and edit.branch_index not in used_branches:
                        used_branches.add(edit.branch_index)
                        edits.append(edit)
                        break
        
        return edits


# ============================================================================
# Natural language description generation (with randomization)
# ============================================================================
def stat_to_natural_language(stat_info):
    """
    Convert circuit statistics to detailed natural language description with randomized phrasing.
    """
    sentences = []
    
    # Circuit topology overview templates
    topology_templates = [
        f"This circuit consists of {stat_info['num_nodes']} nodes and {stat_info['num_branches']} branches.",
        f"The circuit topology features {stat_info['num_nodes']} nodes connected by {stat_info['num_branches']} branches.",
        f"This electrical network is composed of {stat_info['num_nodes']} nodes with {stat_info['num_branches']} branches.",
        f"The circuit structure includes {stat_info['num_nodes']} nodes and {stat_info['num_branches']} interconnecting branches.",
        f"Analyzing the topology, we find {stat_info['num_nodes']} nodes and {stat_info['num_branches']} branches in this circuit.",
    ]
    sentences.append(random.choice(topology_templates))
    
    # Passive components
    passive_parts = []
    if stat_info['num_resistors'] > 0:
        resistor_phrases = [f"{stat_info['num_resistors']} resistor(s)", f"{stat_info['num_resistors']} resistive element(s)"]
        passive_parts.append(random.choice(resistor_phrases))
    if stat_info['num_capacitors'] > 0:
        passive_parts.append(f"{stat_info['num_capacitors']} capacitor(s)")
    if stat_info['num_inductors'] > 0:
        passive_parts.append(f"{stat_info['num_inductors']} inductor(s)")
    
    if passive_parts:
        passive_templates = [
            f"The passive components include {', '.join(passive_parts)}.",
            f"For passive elements, the circuit contains {', '.join(passive_parts)}.",
            f"Regarding passive components, there are {', '.join(passive_parts)}.",
        ]
        sentences.append(random.choice(passive_templates))
    else:
        sentences.append("There are no passive components in this circuit.")
    
    # Independent sources
    source_parts = []
    if stat_info['num_voltage_sources'] > 0:
        source_parts.append(f"{stat_info['num_voltage_sources']} voltage source(s)")
    if stat_info['num_current_sources'] > 0:
        source_parts.append(f"{stat_info['num_current_sources']} current source(s)")
    
    if source_parts:
        source_templates = [
            f"The circuit is powered by {', '.join(source_parts)}.",
            f"For power supply, the circuit has {', '.join(source_parts)}.",
            f"Energy is supplied through {', '.join(source_parts)}.",
        ]
        sentences.append(random.choice(source_templates))
    else:
        sentences.append("No independent sources are present in this circuit.")
    
    # Controlled sources
    if stat_info['num_controlled_sources'] > 0:
        controlled_templates = [
            f"Additionally, {stat_info['num_controlled_sources']} controlled source(s) are present.",
            f"The circuit also features {stat_info['num_controlled_sources']} dependent source(s).",
        ]
        sentences.append(random.choice(controlled_templates))
    else:
        sentences.append("There are no controlled sources in this circuit.")
    
    # Measurements
    meas_parts = []
    if stat_info['num_voltage_measurements'] > 0:
        meas_parts.append(f"{stat_info['num_voltage_measurements']} voltage measurement(s)")
    if stat_info['num_current_measurements'] > 0:
        meas_parts.append(f"{stat_info['num_current_measurements']} current measurement(s)")
    
    if meas_parts:
        sentences.append(f"Measurement setup includes {', '.join(meas_parts)}.")
    else:
        sentences.append("No measurements are configured.")
    
    # Summary
    total_elements = (stat_info['num_resistors'] + stat_info['num_capacitors'] + 
                     stat_info['num_inductors'] + stat_info['num_voltage_sources'] + 
                     stat_info['num_current_sources'] + stat_info['num_controlled_sources'])
    sentences.append(f"In total, this circuit comprises {total_elements} circuit elements.")
    
    return ' '.join(sentences)


# ============================================================================
# LaTeX compilation and file saving utilities
# ============================================================================
def compile_latex_to_png(tex_file_path, output_dir, timeout=120):
    """
    Compile LaTeX file to PNG image using pdflatex and ImageMagick.
    """
    try:
        tex_file_path = os.path.abspath(tex_file_path)
        output_dir = os.path.abspath(output_dir)
        
        tex_filename = os.path.basename(tex_file_path)
        pdf_filename = tex_filename.replace('.tex', '.pdf')
        png_filename = tex_filename.replace('.tex', '.png')
        
        pdf_path = os.path.join(output_dir, pdf_filename)
        png_path = os.path.join(output_dir, png_filename)
        
        # Compile LaTeX to PDF
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_file_path],
            capture_output=True, text=True, timeout=timeout, cwd=output_dir
        )
        
        if not os.path.exists(pdf_path):
            print(f"PDF compilation failed for {tex_file_path}")
            return False
        
        # Convert PDF to PNG using ImageMagick
        magick_cmd = None
        for cmd in ['magick', 'convert']:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
                magick_cmd = cmd
                break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if magick_cmd is None:
            print("ImageMagick not found.")
            return False
        
        convert_cmd = [magick_cmd, '-density', '300', pdf_path, '-quality', '100', 
                      '-background', 'white', '-flatten', png_path]
        subprocess.run(convert_cmd, capture_output=True, text=True, timeout=timeout)
        
        if not os.path.exists(png_path):
            print(f"PNG conversion failed for {pdf_path}")
            return False
        
        # Clean up auxiliary files
        for ext in ['.aux', '.log']:
            aux_file = os.path.join(output_dir, tex_filename.replace('.tex', ext))
            if os.path.exists(aux_file):
                os.remove(aux_file)
        
        return True
        
    except Exception as e:
        print(f"Error compiling {tex_file_path}: {e}")
        return False


def get_stat_info(circuit: Circuit) -> dict:
    """
    Extract statistics from a circuit object.
    """
    return {
        "num_nodes": len(circuit.nodes),
        "num_branches": len(circuit.branches),
        "num_resistors": len([1 for br in circuit.branches if br['type'] == TYPE_RESISTOR]),
        "num_capacitors": len([1 for br in circuit.branches if br['type'] == TYPE_CAPACITOR]),
        "num_inductors": len([1 for br in circuit.branches if br['type'] == TYPE_INDUCTOR]),
        "num_voltage_sources": len([1 for br in circuit.branches if br['type'] == TYPE_VOLTAGE_SOURCE]),
        "num_current_sources": len([1 for br in circuit.branches if br['type'] == TYPE_CURRENT_SOURCE]),
        "num_controlled_sources": len([1 for br in circuit.branches if br['type'] in [TYPE_VCCS, TYPE_VCVS, TYPE_CCCS, TYPE_CCVS]]),
        "num_shorts": len([1 for br in circuit.branches if br['type'] == TYPE_SHORT]),
        "num_voltage_measurements": len([1 for br in circuit.branches if br['type'] == TYPE_RESISTOR and br['measure'] == MEAS_TYPE_VOLTAGE]),
        "num_current_measurements": len([1 for br in circuit.branches if br['type'] == TYPE_RESISTOR and br['measure'] == MEAS_TYPE_CURRENT]),
    }


def save_circuit_files(output_dir: str, latex_code: str, spice_code: str, 
                       stat_info: dict, description: str = None, 
                       edit_instruction: str = None, render_image: bool = True):
    """
    Save circuit files to a directory.
    
    Args:
        output_dir: Directory to save files
        latex_code: LaTeX source code
        spice_code: SPICE netlist code
        stat_info: Circuit statistics
        description: Natural language description (optional)
        edit_instruction: Edit instruction for modified circuits (optional)
        render_image: Whether to render LaTeX to PNG
    
    Returns:
        bool: Success status
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Save LaTeX source
        tex_path = os.path.join(output_dir, "circuit.tex")
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_code)
        
        # Save SPICE code
        spice_path = os.path.join(output_dir, "circuit.sp")
        with open(spice_path, 'w', encoding='utf-8') as f:
            f.write(spice_code)
        
        # Save statistics
        stat_path = os.path.join(output_dir, "stat.json")
        with open(stat_path, 'w', encoding='utf-8') as f:
            json.dump(stat_info, f, indent=2)
        
        # Save description if provided
        if description:
            desc_path = os.path.join(output_dir, "description.txt")
            with open(desc_path, 'w', encoding='utf-8') as f:
                f.write(description)
        
        # Save edit instruction if provided (for edit variants)
        if edit_instruction:
            inst_path = os.path.join(output_dir, "edit_instruction.txt")
            with open(inst_path, 'w', encoding='utf-8') as f:
                f.write(edit_instruction)
        
        # Render image
        if render_image:
            compile_latex_to_png(tex_path, output_dir)
        
        return True
        
    except Exception as e:
        print(f"Error saving circuit files: {e}")
        return False


# ============================================================================
# Main generation logic for circuit editing dataset
# ============================================================================
def generate_edit_dataset_item(circuit_id: str, note: str, output_dir: str, 
                               num_edits: int = 3, render_image: bool = True):
    """
    Generate one complete dataset item: base circuit + multiple edited variants.
    
    Args:
        circuit_id: Unique identifier for this circuit
        note: Version note for circuit generation
        output_dir: Base output directory
        num_edits: Number of edit variants to generate per base circuit
        render_image: Whether to render images
    
    Returns:
        dict: Dataset item metadata
    """
    # Generate base circuit
    while True:
        try:
            base_circuit = gen_circuit(note, id=circuit_id)
            if base_circuit and base_circuit.valid:
                break
        except Exception as e:
            print(f"Error generating circuit: {e}")
            continue
    
    # Get base circuit data
    base_latex = base_circuit.to_latex()
    base_spice = base_circuit._to_SPICE()
    base_stat = get_stat_info(base_circuit)
    base_description = stat_to_natural_language(base_stat)
    
    # Create circuit folder
    circuit_folder = os.path.join(output_dir, circuit_id)
    os.makedirs(circuit_folder, exist_ok=True)
    
    # Save base circuit
    base_folder = os.path.join(circuit_folder, "base")
    save_circuit_files(base_folder, base_latex, base_spice, base_stat, 
                      description=base_description, render_image=render_image)
    
    # Generate edit variants
    edit_generator = EditGenerator(edit_types=[EditGenerator.EDIT_TYPE_PARAMETER])
    edits = edit_generator.generate_edits(base_circuit, num_edits=num_edits)
    
    edit_metadata = []
    for idx, edit in enumerate(edits):
        edit_id = f"edit_{idx + 1}"
        edit_folder = os.path.join(circuit_folder, edit_id)
        
        # Apply edit to get modified circuit
        modified_circuit = edit.apply(base_circuit)
        
        # Regenerate LaTeX and SPICE for modified circuit
        try:
            modified_latex = modified_circuit.to_latex()
            modified_spice = modified_circuit._to_SPICE()
        except Exception as e:
            print(f"Error generating modified circuit output: {e}")
            continue
        
        modified_stat = get_stat_info(modified_circuit)
        edit_instruction = edit.generate_instruction()
        
        # Save edited circuit
        save_circuit_files(edit_folder, modified_latex, modified_spice, modified_stat,
                          edit_instruction=edit_instruction, render_image=render_image)
        
        edit_metadata.append({
            "edit_id": edit_id,
            "edit_type": edit.get_edit_type(),
            "instruction": edit_instruction
        })
    
    # Save metadata for this circuit pair
    metadata = {
        "circuit_id": circuit_id,
        "base_description": base_description,
        "edits": edit_metadata
    }
    
    metadata_path = os.path.join(circuit_folder, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return metadata


def threading_task_edit(task_id, seed, note, gen_num, output_dir, num_edits, render_image):
    """
    Thread worker for generating edit dataset items.
    """
    np.random.seed(seed)
    random.seed(seed)
    
    for i in tqdm(range(gen_num), desc=f"Task {task_id}"):
        circuit_id = f"{task_id}_{i + 1}"
        try:
            generate_edit_dataset_item(
                circuit_id=circuit_id,
                note=note,
                output_dir=output_dir,
                num_edits=num_edits,
                render_image=render_image
            )
            print(f"Generated {circuit_id} with {num_edits} edits")
        except Exception as e:
            print(f"Error generating {circuit_id}: {e}")


# ============================================================================
# Argument parsing and main entry point
# ============================================================================
def parse_args():
    parser = argparse.ArgumentParser(description="Circuit Edit Dataset Generator")
    
    # Basic settings
    parser.add_argument("--note", type=str, default="v11", help="Version note for circuit generation")
    parser.add_argument("--gen_num", type=int, default=100, help="Number of base circuits to generate")
    parser.add_argument("--output_dir", type=str, default="./data/edit_dataset", 
                        help="Output directory for dataset")
    
    # Edit settings
    parser.add_argument("--num_edits", type=int, default=3, 
                        help="Number of edit variants per base circuit")
    
    # Processing settings
    parser.add_argument("--num_proc", type=int, default=1, help="Number of parallel threads")
    parser.add_argument("--render_image", action="store_true", default=True,
                        help="Whether to render LaTeX to PNG")
    parser.add_argument("--no_render", action="store_true", default=False,
                        help="Disable image rendering (faster for testing)")
    
    args = parser.parse_args()
    
    # Handle render flag
    if args.no_render:
        args.render_image = False
    
    return args


def main(args):
    """
    Main function to generate circuit edit dataset.
    """
    note = args.note
    gen_num = args.gen_num
    output_dir = os.path.abspath(args.output_dir)
    num_edits = args.num_edits
    num_proc = args.num_proc
    render_image = args.render_image
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print(f"Generating {gen_num} circuits with {num_edits} edits each")
    print(f"Using {num_proc} threads, render_image={render_image}")
    
    # Run generation
    with ThreadPoolExecutor(max_workers=num_proc) as executor:
        tasks_per_thread = gen_num // num_proc
        for i in range(1, num_proc + 1):
            executor.submit(
                threading_task_edit, 
                i, i, note, tasks_per_thread, output_dir, num_edits, render_image
            )
    
    print(f"\nGeneration complete! Dataset saved to: {output_dir}")
    print(f"Structure: {output_dir}/<circuit_id>/base/ + edit_1/ + edit_2/ + ...")


if __name__ == '__main__':
    args = parse_args()
    main(args)
# # 3) 生成数据（示例：生成5个基础电路，每个3个参数修改版，4线程）
# python generate.py --note v11 --gen_num 5 --num_edits 3 --num_proc 4 --output_dir ./data/edit_dataset