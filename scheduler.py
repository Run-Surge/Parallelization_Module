import json
import os
import argparse

# ==============================================================================
# 2. CORE MEMORY CALCULATION LOGIC
# ==============================================================================
def calculate_peak_memory_for_statements(statements, live_vars_data, func_footprints_data, stmt_to_idx_map):
    """Calculates the true peak memory for a list of statements by simulating its execution."""
    peak_memory_for_block = 0
    for stmt in statements:
        live_vars_at_line = live_vars_data.get(stmt, {})
        sum_of_live_vars = sum(var_info['size'] for var_info in live_vars_at_line.values())
        
        func_execution_size = 0
        original_idx = stmt_to_idx_map.get(stmt)
        if original_idx is not None:
            key_prefix_to_find = f"{stmt}"
            found_key = next((k for k in func_footprints_data if k.startswith(key_prefix_to_find)), None)
            if found_key:
                func_mem_dict = func_footprints_data[found_key]
                if func_mem_dict:
                    func_execution_size = list(func_mem_dict.values())[-1]
        
        instantaneous_memory = sum_of_live_vars + func_execution_size
        if instantaneous_memory > peak_memory_for_block:
            peak_memory_for_block = instantaneous_memory
    return peak_memory_for_block

# ==============================================================================
# 3. SCHEDULING ALGORITHMS
# ==============================================================================
def schedule_program_whole(program_statements, nodes_data, live_vars_data, func_footprints_data, stmt_to_idx_map):
    """Attempt 1: Tries to schedule the entire program as one single block."""
    print("--- Attempt 1: Scheduling the entire program on a single node ---")
    
    peak_memory = calculate_peak_memory_for_statements(program_statements, live_vars_data, func_footprints_data, stmt_to_idx_map)
    print(f"Peak memory requirement for the whole program is: {peak_memory}")

    sorted_nodes = sorted(nodes_data, key=lambda x: x['memory'])
    fitting_node = next((node for node in sorted_nodes if node['memory'] >= peak_memory), None)
    
    if fitting_node:
        print(f"SUCCESS: Program fits on '{fitting_node['name']}' (Memory: {fitting_node['memory']}).")
    else:
        print("FAILURE: No single node has enough memory for the entire program.")
        
    return fitting_node

def process_and_merge_blocks(blocks_data, nodes_data, func_footprints_data, live_vars_data):
    """Attempt 2: Merges blocks based on dependencies and memory, then schedules the final blocks."""
    print("\n--- Attempt 2: Merging execution blocks to find a feasible schedule ---")
    
    if not nodes_data:
        print("Error: No node data provided.")
        return blocks_data, []
    max_node_memory = max(node['memory'] for node in nodes_data)
    print(f"System's Maximum Node Memory for merging: {max_node_memory}")
    
    stmt_to_idx_map = {stmt: i for i, block in enumerate(blocks_data) for stmt in block['statements']}
    output_folder = "pass_trace_outputs"
    os.makedirs(output_folder, exist_ok=True)
    print(f"Tracing pass outputs to the '{output_folder}' directory.")
    
    blocks = json.loads(json.dumps(blocks_data)) 
    merged_in_pass, pass_num = True, 1
    
    while merged_in_pass:
        print(f"\n--- Starting Pass #{pass_num} ---")
        merged_in_pass = False
        source_idx = 0
        while source_idx < len(blocks):
            current_block, did_merge_and_restart = blocks[source_idx], False
            for key_str in current_block['key']:
                target_idx = -1
                try:
                    var, index_str = key_str.split(':')
                    if var != 'none' and index_str != 'none' and int(index_str) != source_idx:
                        target_idx = int(index_str)
                except (ValueError, IndexError): continue
                if target_idx == -1: continue

                target_block = blocks[target_idx]
                temp_merged_statements = target_block['statements'] + current_block['statements']
                merged_footprint = calculate_peak_memory_for_statements(temp_merged_statements, live_vars_data, func_footprints_data, stmt_to_idx_map)
                
                if merged_footprint <= max_node_memory:
                    print(f"  -> Merge PASSED: block {source_idx} -> block {target_idx} (New Peak: {merged_footprint})")
                    target_block['statements'].extend(current_block['statements'])
                    inherited_keys = [k for k in current_block['key'] if k.split(':')[-1] != str(target_idx)]
                    target_block['key'] = list(dict.fromkeys(target_block['key'] + inherited_keys))
                    blocks.pop(source_idx)
                    for block_to_update in blocks:
                        block_to_update['key'] = [
                            f"{k.split(':')[0]}:{int(k.split(':')[1]) - 1}" if k.split(':')[1].isdigit() and int(k.split(':')[1]) > source_idx
                            else f"{k.split(':')[0]}:{target_idx if target_idx < source_idx else target_idx - 1}" if k.split(':')[1].isdigit() and int(k.split(':')[1]) == source_idx
                            else k
                            for k in block_to_update['key']
                        ]
                    merged_in_pass, did_merge_and_restart = True, True
                    break
                else:
                    print(f"  -> Merge FAILED: block {source_idx} -> block {target_idx} (New Peak: {merged_footprint})")
            if did_merge_and_restart: break
            else: source_idx += 1
        
        pass_output_filename = os.path.join(output_folder, f"pass_{pass_num}_output.json")
        with open(pass_output_filename, 'w') as f: json.dump(blocks, f, indent=4)
        print(f"  -> Wrote state of Pass #{pass_num} to '{pass_output_filename}'")
        pass_num += 1

    print("\n--- Merging Complete. Calculating final scheduling info. ---")
    block_scheduling_info = []
    sorted_nodes = sorted(nodes_data, key=lambda x: x['memory'])
    for i, block in enumerate(blocks):
        final_peak_memory = calculate_peak_memory_for_statements(block['statements'], live_vars_data, func_footprints_data, stmt_to_idx_map)
        fitting_node = next((node for node in sorted_nodes if node['memory'] >= final_peak_memory), None)
        block_scheduling_info.append({"block_index": i, "statements": block['statements'], "peak_memory": final_peak_memory, "fitting_node": fitting_node})
        print(f"Final Block {i}: Peak Memory = {final_peak_memory}, Recommended Node = {fitting_node['name'] if fitting_node else 'None'}")
    return blocks, block_scheduling_info

# ==============================================================================
# 4. MAIN EXECUTION BLOCK
# ==============================================================================
def main():
    """Main function to parse arguments and run the scheduling workflow."""
    parser = argparse.ArgumentParser(
        description="A smart scheduler that first tries to fit a whole program, then resorts to merging blocks.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('blocks_file', help='Path to the initial blocks definition JSON file.')
    parser.add_argument('live_vars_file', help='Path to live variables JSON file.')
    parser.add_argument('func_footprints_file', help='Path to function footprints JSON file.')
    parser.add_argument('nodes_file', help='Path to nodes JSON file.')
    parser.add_argument('--generate-test-files', action='store_true', help='Generate test JSON files with default names before running.')
    args = parser.parse_args()

    # --- Load all data from files ---
    try:
        with open(args.blocks_file, 'r') as f: initial_blocks = json.load(f)
        with open(args.live_vars_file, 'r') as f: live_vars_data = json.load(f)
        with open(args.func_footprints_file, 'r') as f: func_footprints_data = json.load(f)
        with open(args.nodes_file, 'r') as f: nodes_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Could not find required input file: {e.filename}")
        return

    # --- Prepare necessary data structures ---
    full_program_statements = [stmt for block in initial_blocks for stmt in block['statements']]
    stmt_to_original_idx_map = {stmt: i for i, block in enumerate(initial_blocks) for stmt in block['statements']}
    
    # --- Execute the scheduling workflow ---
    whole_program_node = schedule_program_whole(full_program_statements, nodes_data, live_vars_data, func_footprints_data, stmt_to_original_idx_map)

    if not whole_program_node:
        # If the first attempt failed, run the merging process
        final_blocks, scheduling_info = process_and_merge_blocks(initial_blocks, nodes_data, func_footprints_data, live_vars_data)
        
        # Save the final outputs from the merging process
        with open("final_merged_blocks_output.json", 'w') as f: json.dump(final_blocks, f, indent=4)
        with open("block_scheduling_info.json", 'w') as f: json.dump(scheduling_info, f, indent=4)
        print("\nMerging process complete. See output files for results.")

if __name__ == '__main__':
    main()