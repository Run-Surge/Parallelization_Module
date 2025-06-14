import json
import argparse
import ast
import re
import math

# ==============================================================================
# 1. CORE MEMORY CALCULATION LOGIC
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
# 1.1. CONTEXT-AWARE MEMORY CALCULATION
# ==============================================================================
def calculate_peak_memory_for_merged_block(
    block_statements,
    block_keys,
    live_vars_data,
    func_footprints_data,
    stmt_to_idx_map
):
    """
    Calculates the peak memory for a specific block (or a potential merged block),
    considering only its external dependencies (from keys) and internally created variables.
    """
    peak_memory_for_block = 0
    # A simple way to parse the variable being created (e.g., "z" from "z = add1(data)")
    get_lhs_var = lambda s: s.split(' ')[0]

    # These are the input variables the block depends on from the outside.
    external_dependency_vars = {k.split(':')[0] for k in block_keys if k.split(':')[0] != 'none'}

    for i, stmt in enumerate(block_statements):
        # 1. Get the memory cost of the function call itself.
        func_execution_size = 0
        original_idx = stmt_to_idx_map.get(stmt)
        if original_idx is not None:
            key_prefix_to_find = f"{stmt}"
            found_key = next((k for k in func_footprints_data if k.startswith(key_prefix_to_find)), None)
            if found_key and func_footprints_data[found_key]:
                func_execution_size = list(func_footprints_data[found_key].values())[-1]

        # 2. Identify all variables that should be live at this point *within this block's context*.
        # These are the external dependencies PLUS any variables created in previous statements of this block.
        internal_vars_so_far = {get_lhs_var(s) for s in block_statements[:i]}
        relevant_vars = external_dependency_vars.union(internal_vars_so_far)

        # 3. Sum the sizes of only these relevant live variables.
        # We look up their sizes in the global live_vars_data for the current statement.
        live_vars_at_line = live_vars_data.get(stmt, {})
        sum_of_relevant_live_vars = sum(
            var_info['size'] for var_name, var_info in live_vars_at_line.items()
            if var_name in relevant_vars
        )

        # 4. Calculate total instantaneous memory and update the peak.
        instantaneous_memory = sum_of_relevant_live_vars + func_execution_size
        if instantaneous_memory > peak_memory_for_block:
            peak_memory_for_block = instantaneous_memory
            
    return peak_memory_for_block

# ==============================================================================
# 2. SCHEDULING ALGORITHMS
# ==============================================================================
def schedule_program_whole(program_statements, nodes_data, live_vars_data, func_footprints_data, stmt_to_idx_map):
    """Attempt 1: Tries to schedule the entire program as one single block."""
    print("--- Attempt 1: Scheduling the entire program on a single node ---")
    
    peak_memory = calculate_peak_memory_for_statements(program_statements, live_vars_data, func_footprints_data, stmt_to_idx_map)
    print(f"Peak memory requirement for the whole program is: {peak_memory}")

    sorted_nodes = sorted(nodes_data, key=lambda x: x['memory'])
    print(sorted_nodes)
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
    
    # This map is crucial and must be based on the original blocks_data, not the changing 'blocks' list
    stmt_to_idx_map = {stmt: i for i, block in enumerate(blocks_data) for stmt in block['statements']}
    
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
                
                # --- MODIFIED LOGIC START ---
                temp_merged_statements = target_block['statements'] + current_block['statements']
                # Combine keys for the temporary merged block to check its dependencies accurately
                temp_merged_keys = list(dict.fromkeys(target_block['key'] + current_block['key']))

                # Use the new, context-aware memory calculation function
                merged_footprint = calculate_peak_memory_for_merged_block(
                    temp_merged_statements,
                    temp_merged_keys,
                    live_vars_data,
                    func_footprints_data,
                    stmt_to_idx_map
                )
                # --- MODIFIED LOGIC END ---
                
                if merged_footprint <= max_node_memory:
                    print(f"  -> Merge PASSED: block {source_idx} -> block {target_idx} (New Peak: {merged_footprint})")
                    target_block['statements'].extend(current_block['statements'])
                    inherited_keys = [k for k in current_block['key'] if k.split(':')[-1] != str(target_idx)]
                    target_block['key'] = list(dict.fromkeys(target_block['key'] + inherited_keys))
                    blocks.pop(source_idx)
                    # This key re-indexing logic remains the same
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
        
        pass_num += 1

    print("\n--- Merging Complete. Calculating final scheduling info. ---")
    block_scheduling_info = []
    sorted_nodes = sorted(nodes_data, key=lambda x: x['memory'])
    for i, block in enumerate(blocks):
        # --- MODIFIED LOGIC START ---
        # Also use the new function for the final calculation
        final_peak_memory = calculate_peak_memory_for_merged_block(
            block['statements'],
            block['key'],
            live_vars_data,
            func_footprints_data,
            stmt_to_idx_map
        )
        # --- MODIFIED LOGIC END ---

        fitting_node = next((node for node in sorted_nodes if node['memory'] >= final_peak_memory), None)
        block_scheduling_info.append({"block_index": i, "statements": block['statements'], "peak_memory": final_peak_memory, "fitting_node": fitting_node})
        print(f"Final Block {i}: Peak Memory = {final_peak_memory}, Recommended Node = {fitting_node['name'] if fitting_node else 'None'}")
    return blocks, block_scheduling_info

# ==============================================================================
# 3. CONSOLIDATION AND SCHEDULING INFO
# ==============================================================================
def consolidate_to_block_format(
    final_blocks,
    scheduling_info,
    nodes_data,
    live_vars_data,
    func_footprints_data,
    stmt_to_idx_map
):
    """
    Consolidates contiguous schedulable blocks, but ONLY if the resulting
    merged block still fits on an available node.
    """
    print("\n--- Post-Processing: Consolidating and re-mapping keys for final schedule ---")

    if not nodes_data:
        print("Error: No node data provided. Cannot perform consolidation.")
        return final_blocks, scheduling_info

    # Determine the maximum memory available in the system
    max_node_memory = max(node['memory'] for node in nodes_data)
    print(f"System's Maximum Node Memory for consolidation: {max_node_memory}")

    if not any(info['fitting_node'] for info in scheduling_info):
        print("No schedulable blocks found. No consolidation performed.")
        # ... (same handling as before for no schedulable blocks)
        return final_blocks, scheduling_info

    # --- Phase 1: Group contiguous schedulable blocks CONDITIONALLY ---
    preliminary_blocks = []
    old_to_new_index_map = {}
    i = 0
    while i < len(final_blocks):
        is_schedulable = scheduling_info[i].get('fitting_node') is not None
        
        if is_schedulable:
            # Start a new potential group with the current block.
            current_group = {
                "key": list(final_blocks[i]["key"]),
                "statements": list(final_blocks[i]["statements"])
            }
            new_idx = len(preliminary_blocks)
            old_to_new_index_map[i] = new_idx
            
            # Look ahead to the *next* blocks to see if we can merge them.
            j = i + 1
            while j < len(final_blocks) and (scheduling_info[j].get('fitting_node') is not None):
                potential_next_block = final_blocks[j]
                
                # --- SIMULATE THE MERGE ---
                temp_merged_statements = current_group["statements"] + potential_next_block["statements"]
                # Combine keys for accurate context-aware calculation
                temp_merged_keys = list(set(current_group["key"] + potential_next_block["key"]))

                simulated_peak = calculate_peak_memory_for_merged_block(
                    temp_merged_statements, temp_merged_keys, live_vars_data, func_footprints_data, stmt_to_idx_map
                )

                # --- CHECK IF THE MERGE IS VALID ---
                if simulated_peak <= max_node_memory:
                    print(f"  -> Merge SIMULATION PASSED: block {j} into group starting at {i} (New Peak: {simulated_peak})")
                    # The merge is valid, so commit it.
                    current_group["statements"] = temp_merged_statements
                    current_group["key"] = temp_merged_keys
                    old_to_new_index_map[j] = new_idx
                    j += 1 # Move on to try the next block
                else:
                    print(f"  -> Merge SIMULATION FAILED: block {j} into group starting at {i} (New Peak: {simulated_peak} > {max_node_memory})")
                    # The merge would create a block that is too large. Stop growing this group.
                    break
            
            preliminary_blocks.append(current_group)
            i = j # IMPORTANT: Advance the main loop counter past all merged blocks
        else:
            # This is an unschedulable block, add it as-is
            new_idx = len(preliminary_blocks)
            preliminary_blocks.append(final_blocks[i])
            old_to_new_index_map[i] = new_idx
            i += 1

    # --- Phase 2: Iterate through the new structure and rewrite all keys using the map ---
    final_consolidated_blocks = []
    for new_idx, block in enumerate(preliminary_blocks):
        updated_keys = set() # Use a set to handle duplicates automatically
        for key_str in block['key']:
            try:
                var, index_str = key_str.split(':')
                if index_str == 'none':
                    updated_keys.add(key_str)
                    continue
                
                old_dep_index = int(index_str)
                # Find the new index that the old dependency now maps to
                new_dep_index = old_to_new_index_map.get(old_dep_index)
                
                # Only keep the key if it points to a DIFFERENT consolidated block
                if new_dep_index is not None and new_dep_index != new_idx:
                    updated_keys.add(f"{var}:{new_dep_index}")
            except (ValueError, IndexError):
                updated_keys.add(key_str) # Keep malformed keys as is
                
        final_consolidated_blocks.append({
            "key": sorted(list(updated_keys)), # Sort for consistent output
            "statements": block["statements"]
        })

    # --- Phase 3: Calculate final info for the newly consolidated blocks ---
    consolidated_schedule_info = []
    sorted_nodes = sorted(nodes_data, key=lambda x: x['memory'])
    
    for i, block in enumerate(final_consolidated_blocks):
        if block['statements']:
            # Use the correct peak memory calculation for the now-contiguous block
            peak_memory = calculate_peak_memory_for_merged_block(
                block['statements'], block['key'], live_vars_data, func_footprints_data, stmt_to_idx_map
            )
            fitting_node = next((node for node in sorted_nodes if node['memory'] >= peak_memory), None)
            
            consolidated_schedule_info.append({
                "consolidated_block_index": i,
                "peak_memory": peak_memory,
                "assigned_node": fitting_node,
                "is_schedulable": fitting_node is not None,
                "key": block['key'],
                "statements": block['statements']
            })
        else:
             consolidated_schedule_info.append({
                "consolidated_block_index": i,
                "peak_memory": 0, "assigned_node": None, "is_schedulable": False,
                "key": block['key'], "statements": block['statements']
            })

    return final_consolidated_blocks, consolidated_schedule_info

# ==============================================================================
# 4. PARALLELIZATION WITH DEFERRAL LOGIC
# ==============================================================================
def get_iterable_name(node):
    """Safely gets the variable name from a for-loop's iterable node."""
    if isinstance(node, ast.Name):
        return node.id
    return None

def is_infeasible_due_to_nested_loops(py_source_code, arg_names):
    try:
        tree = ast.parse(py_source_code)
    except SyntaxError as e:
        # It hits this exception because of the bad indentation!
        print(f"  Warning: Could not parse reconstructed source code...")
        return True # It returns True (infeasible) on any syntax error
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            for inner_node in ast.walk(node):
                if inner_node is node:
                    continue
                if isinstance(inner_node, ast.For):
                    iterable_var = get_iterable_name(inner_node.iter)
                    if iterable_var and iterable_var in arg_names:
                        print(f"  -> Feasibility Check FAILED: Found nested loop where inner loop iterates over argument '{iterable_var}'.")
                        return True
    return False

def reconstruct_source_with_indentation(lines_of_code):
    """
    Reconstructs a Python source string with plausible indentation.
    This version correctly handles keys that are multi-line strings.
    """
    reconstructed_code = []
    indent_level = 0
    DEDENT_KEYWORDS = ('elif', 'else:', 'except', 'finally')

    # First, flatten the list so that multi-line keys become multiple items
    actual_lines = []
    for key in lines_of_code:
        actual_lines.extend(key.split('\n'))

    for line in actual_lines:
        stripped_line = line.strip()
        if not stripped_line: # Skip empty lines
            continue
        
        # Check for dedentation before applying current indent
        if stripped_line.startswith(DEDENT_KEYWORDS):
            indent_level = max(0, indent_level - 1)

        reconstructed_code.append(("    " * indent_level) + stripped_line) # Use 4 spaces for clarity

        # Check for indentation for the *next* line
        if stripped_line.endswith(':'):
            indent_level += 1
            
    return "\n".join(reconstructed_code)

def plan_data_parallelization(
    unschedulable_blocks,
    nodes_data,
    live_vars_data,
    func_footprints_data
):
    """
    For unschedulable blocks, determines if a parallelization plan can be made
    statically or if the decision must be deferred.

    - If a block has NO dependencies on other blocks (keys are all 'var:none'),
      it attempts to create a parallelization plan.
    - If a block HAS a dependency, it is flagged as 'Deferred: Requires Feedback'.
    """
    print("\n--- Level 3: Planning Data Parallelization for Failed Blocks ---")
    
    # ... (Keep the helper functions: reconstruct_source_with_indentation, is_infeasible_due_to_nested_loops, etc.) ...
    
    if not unschedulable_blocks:
        print("No unschedulable blocks to process at this level.")
        return {}
    if not nodes_data:
        print("Error: No node data available for parallelization planning.")
        return {}
        
    sorted_nodes = sorted(nodes_data, key=lambda x: x['memory'])
    smallest_node_memory = sorted_nodes[0]['memory']
    print(f"Using smallest node '{sorted_nodes[0]['name']}' with {smallest_node_memory} memory as baseline.")

    parallelization_plan = {}
    for block in unschedulable_blocks:
        if not block['statements']:
            continue
        
        statement = block['statements'][0]
        print(f"\nAnalyzing: '{statement}'")

        # --- NEW GATING LOGIC ---
        # First, check if the block has any real dependencies.
        block_keys = block.get('key', [])
        # A real dependency exists if any key has a numeric index part.
        has_real_dependency = any(
            k.split(':')[1].isdigit() for k in block_keys if ':' in k
        )

        if has_real_dependency:
            print(f"  -> DEFERRED: Block depends on preceding blocks {block_keys}. Flagging for feedback.")
            parallelization_plan[statement] = {
                "status": "Deferred: Requires Feedback",
                "reason": "This block depends on the output of a preceding block, which must be evaluated first.",
                "dependencies": block_keys
            }
            continue # Skip to the next unschedulable block

        # --- If we get here, the block has no preceding dependencies. We can try to plan it. ---
        print("  -> No preceding dependencies. Attempting parallelization plan.")
        
        match = re.match(r"[\w\s,.]+\s*=\s*([\w.]+)\((.*)\)", statement)
        if not match:
            print(f"  -> Could not parse function and args from statement. Skipping.")
            parallelization_plan[statement] = {"status": "Failed", "reason": "Could not parse statement."}
            continue
            
        func_name_or_method, args_str = match.groups()
        arg_names = [arg.strip() for arg in args_str.split(',') if arg.strip()]

        found_key = next((k for k in func_footprints_data if k.startswith(statement)), None)
        if not found_key:
            print(f"  -> Feasibility Check FAILED: No function footprint data found for '{statement}'.")
            parallelization_plan[statement] = {"status": "Failed: Infeasible", "reason": "No footprint data found to reconstruct source."}
            continue
            
        lines_from_footprints = [line for line in func_footprints_data[found_key].keys() if line != "aggregation"]
        source_code = reconstruct_source_with_indentation(lines_from_footprints)
        
        if is_infeasible_due_to_nested_loops(source_code, arg_names):
            parallelization_plan[statement] = {"status": "Failed: Infeasible", "reason": "Function contains an argument in a nested loop iterable."}
            continue
            
        print("  -> Feasibility Check PASSED.")

        # --- The rest of the calculation logic proceeds as before ---
        live_vars_at_line = live_vars_data.get(statement, {})
        # ... (and so on) ...

        sum_of_args_size = sum(live_vars_at_line[arg]['size'] for arg in arg_names if arg in live_vars_at_line)
        mem_values = [v for v in func_footprints_data[found_key].values() if isinstance(v, (int, float))]
        func_execution_size = mem_values[-1] if mem_values else 0
        total_required_mem = sum_of_args_size + func_execution_size
        num_chunks = math.ceil(total_required_mem / smallest_node_memory)
        
        if num_chunks <= 1: num_chunks = 2 

        print(f"  -> Required Memory: {total_required_mem}, Smallest Node: {smallest_node_memory} -> Parallelization Factor: {num_chunks}")

         # --- REVISED LOGIC: Define Chunks For Each Argument ---
        chunks_per_argument = {}
        # Iterate through each argument that was parsed from the function call
        for arg_name in arg_names:
            arg_info = live_vars_at_line.get(arg_name)

            # Only create chunks for arguments that have a 'length' attribute
            if not arg_info or 'length' not in arg_info:
                print(f"  -> Argument '{arg_name}' is not parallelizable (no length data). Skipping.")
                continue

            total_length = arg_info['length']
            
            # Cannot create more chunks than there are items in this specific argument
            effective_num_chunks = min(num_chunks, total_length if total_length > 0 else 1)
            if effective_num_chunks == 0 and total_length > 0: effective_num_chunks = 1
            if effective_num_chunks == 0: continue

            # Calculate the chunk size specifically for this argument
            chunk_size = math.ceil(total_length / effective_num_chunks)
            
            arg_chunks_list = []
            for i in range(effective_num_chunks):
                start_index = i * chunk_size
                end_index = min((i + 1) * chunk_size, total_length)
                arg_chunks_list.append({"chunk_id": i, "start_index": start_index, "end_index": end_index})
                if end_index >= total_length:
                    break # Stop if we've covered the entire length of this argument
            
            chunks_per_argument[arg_name] = arg_chunks_list
            print(f"  -> Defined {len(arg_chunks_list)} chunks for argument '{arg_name}' (length: {total_length}).")

        parallelization_plan[statement] = {
            "status": "Success",
            "parallelization_factor": num_chunks, # The overall target number of parallel jobs
            "chunks": chunks_per_argument # The new, detailed chunking dictionary
        }

    return parallelization_plan

# ==============================================================================
# 5. FINAL EXECUTION PLAN GENERATION
# ==============================================================================
def generate_execution_plan(
    consolidated_schedule_info,
    parallelization_plan,
    nodes_data
):
    """
    Generates a master schedule and individual instruction files for each node,
    including synchronization hints and parallel execution plans.
    """
    print("\n--- Generating Final Execution Plan ---")
    
    # Initialize plans for each node and the master schedule
    node_plans = {node['name']: [] for node in nodes_data}
    master_plan = ["# Master Execution Schedule\n"]
    
    # Helper to get the variable on the left-hand side of an assignment
    get_lhs_var = lambda s: s.split('=')[0].strip()

    # --- Step 1: Map blocks to their assigned nodes for easy dependency lookup ---
    block_to_node_map = {
        info['consolidated_block_index']: info['assigned_node']['name']
        for info in consolidated_schedule_info if info['is_schedulable']
    }
    
    # --- Step 2: Process all blocks from the consolidated schedule ---
    for i, info in enumerate(consolidated_schedule_info):
        block_idx = info['consolidated_block_index']
        
        # --- CASE A: The block is schedulable and has a definite assignment ---
        if info['is_schedulable']:
            node_name = info['assigned_node']['name']
            master_plan.append(f"--- BLOCK {block_idx} (On {node_name}) ---")
            
            node_plans[node_name].append(f"\n# --- Task: Execute Block {block_idx} ---")
            
            # Add synchronization hints by checking dependencies
            for key in info['key']:
                var, source_idx_str = key.split(':')
                if source_idx_str.isdigit():
                    source_idx = int(source_idx_str)
                    if source_idx in block_to_node_map:
                        source_node = block_to_node_map[source_idx]
                        sync_msg = f"WAIT for variable '{var}' from Node: {source_node}"
                        node_plans[node_name].append(sync_msg)
                        master_plan.append(f"  - {node_name} must WAIT for '{var}' from {source_node}")
            
            # Add the actual execution statements
            for stmt in info['statements']:
                node_plans[node_name].append(f"RUN: {stmt}")
            
            master_plan.append(f"  - {node_name} executes {len(info['statements'])} statement(s).")
            node_plans[node_name].append(f"# --- End Block {block_idx} ---")

        # --- CASE B: The block is unschedulable, consult the parallelization plan ---
        else:
            if not info['statements']: continue
            
            statement = info['statements'][0]
            plan = parallelization_plan.get(statement)
            
            if not plan:
                master_plan.append(f"--- Task '{statement}' (UNHANDLED) ---")
                master_plan.append("  - No valid plan found for this unschedulable block.")
                continue

            master_plan.append(f"--- Task '{statement}' (Unscheduled) ---")

            # Subcase B1: The task is deferred for a feedback loop
            if plan['status'] == "Deferred: Requires Feedback":
                master_plan.append("  - STATUS: DEFERRED, requires runtime feedback.")
                master_plan.append(f"  - REASON: {plan['reason']}")

            # Subcase B2: The task can be parallelized
            elif plan['status'] == "Success":
                master_plan.append("  - STATUS: To be executed in PARALLEL.")
                
                # A. Identify free nodes and designate an aggregator
                primary_busy_nodes = set(block_to_node_map.values())
                free_nodes = [node for node in nodes_data if node['name'] not in primary_busy_nodes]
                if not free_nodes: # If all nodes are busy, use all of them as workers
                    free_nodes = sorted(nodes_data, key=lambda n: n['memory'], reverse=True)
                
                aggregator_node = free_nodes[0]['name']
                worker_nodes = [n['name'] for n in free_nodes]
                
                master_plan.append(f"  - Aggregator Node: {aggregator_node}")
                master_plan.append(f"  - Worker Nodes: {', '.join(worker_nodes)}")

                # B. Add aggregation task to the aggregator node's plan
                output_var = get_lhs_var(statement)
                node_plans[aggregator_node].append(f"\n# --- Task: Aggregate results for '{output_var}' ---")
                node_plans[aggregator_node].append(f"WAIT for results from all workers for '{statement}'")
                node_plans[aggregator_node].append(f"RUN: {output_var} = aggregate_results()")
                node_plans[aggregator_node].append(f"# --- End Aggregation ---")

                # C. Distribute chunks and generate worker instructions
                chunk_details = plan.get('chunks', {})
                all_chunk_ids = list(range(plan.get('parallelization_factor', 0)))

                for i, chunk_id in enumerate(all_chunk_ids):
                    worker_node = worker_nodes[i % len(worker_nodes)] # Round-robin assignment
                    
                    if i == 0: # Add header and sync hints only for the first chunk on any worker
                        node_plans[worker_node].append(f"\n# --- Task: Parallel execution for '{statement}' ---")
                        # Add sync hints for the *initial data* needed for this parallel task
                        for key in info['key']:
                            var, source_idx_str = key.split(':')
                            if source_idx_str.isdigit():
                                source_idx = int(source_idx_str)
                                if source_idx in block_to_node_map:
                                    source_node = block_to_node_map[source_idx]
                                    node_plans[worker_node].append(f"WAIT for variable '{var}' from Node: {source_node}")
                    
                    master_plan.append(f"  - Node {worker_node} assigned to run chunk {chunk_id}.")
                    node_plans[worker_node].append(f"# -- Chunk {chunk_id} --")
                    for arg_name, chunks in chunk_details.items():
                        if chunk_id < len(chunks):
                            chunk_info = chunks[chunk_id]
                            start, end = chunk_info['start_index'], chunk_info['end_index']
                            node_plans[worker_node].append(f"RUN task on chunk of '{arg_name}', indices {start}:{end}")
                
                # Add the final 'send' instruction to all workers
                for worker in set(worker_nodes):
                    node_plans[worker].append(f"SEND results to aggregator: {aggregator_node}")
                    node_plans[worker].append(f"# --- End Parallel Task ---")

    # --- Step 3: Write all generated plans to files ---
    try:
        # Write the master plan
        with open("master_schedule.txt", "w") as f:
            f.write("\n".join(master_plan))
        print("Master schedule written to master_schedule.txt")

        # Write individual node plans
        for node_name, plan_steps in node_plans.items():
            if not plan_steps: continue # Don't create empty files
            with open(f"{node_name}.txt", "w") as f:
                f.write("\n".join(plan_steps))
            print(f"Execution plan for {node_name} written to {node_name}.txt")

    except IOError as e:
        print(f"Error writing execution plan files: {e}")
    
    

# ==============================================================================
# 6. MAIN EXECUTION BLOCK
# ==============================================================================
def main():
    """Main function to parse arguments and run the scheduling workflow."""
    parser = argparse.ArgumentParser(
        description="A smart scheduler that first tries to fit a whole program, then resorts to merging blocks.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # ... (keep all your argument parsing code here) ...
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
    
    # Initialize variables for the report
    if not whole_program_node:
        # If the first attempt failed, run the merging process
        final_blocks, scheduling_info = process_and_merge_blocks(initial_blocks, nodes_data, func_footprints_data, live_vars_data)

        # Run the post-processing and consolidation step
        consolidated_schedule, consolidated_schedule_info = consolidate_to_block_format(
            final_blocks,
            scheduling_info,
            nodes_data,          # Pass nodes_data
            live_vars_data,      # Pass live_vars_data
            func_footprints_data,# Pass func_footprints_data
            stmt_to_original_idx_map      # Pass stmt_to_idx_map
        )

        # --- LEVEL 3: ATTEMPT DATA PARALLELIZATION ---
        unschedulable_final_blocks = [
            info for info in consolidated_schedule_info if not info['is_schedulable']
        ]

        parallelization_plan = plan_data_parallelization(
            unschedulable_final_blocks,
            nodes_data,
            live_vars_data,
            func_footprints_data,
        )

        # --- FINAL STEP: GENERATE EXECUTION PLAN ---
        generate_execution_plan(
            consolidated_schedule_info,
            parallelization_plan,
            nodes_data
        )

        # --- OUTPUTS ---
        # with open("final.json", 'w') as f:
        #     json.dump(final_blocks, f, indent=4)
        # with open("blocks.json", 'w') as f:
        #     json.dump(scheduling_info, f, indent=4)
        with open("final_schedule_info.json", 'w') as f:
            json.dump(consolidated_schedule_info, f, indent=4)
        with open("consolidated_schedule.json", 'w') as f:
            json.dump(consolidated_schedule, f, indent=4)
        with open("parallelization_plan.json", 'w') as f:
            json.dump(parallelization_plan, f, indent=4)
        print(f"\nFinal consolidated schedule has been written to 'final_schedule_info.json'")
        print("\nData parallelization plan has been written to 'parallelization_plan.json'")

if __name__ == '__main__':
    main()