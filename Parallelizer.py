from Memory_Estimator import *
from DDG import *
import py_compile
import sys
from collections import defaultdict, deque
from typing import List, Dict, Any
import glob
import json



def group_by_needs_with_wait_index(
    statements: List[Dict[str, Any]],
    dependency_graph: Dict[str, Any]
) -> List[List[str]]:
    # 1) Map code_line → produced variables
    produced = {s["code line"]: s["has"] for s in statements}

    # 2) Build var → producer_line map
    var_to_producer_line = {}
    for line, has_vars in produced.items():
        for v in has_vars:
            var_to_producer_line[v] = line

    # 3) Map each statement to its sorted-needs tuple
    needs_map = {
        s["code line"]: tuple(sorted(s["needs"]))
        for s in statements
    }

    # 4) Bucket statements by that needs tuple
    buckets = defaultdict(list)
    for s in statements:
        tpl = needs_map[s["code line"]]
        buckets[tpl].append(s)

    # 5) Prepare ordering of distinct needs‐tuples
    distinct = list(buckets.keys())

    def needs_key(need_tpl):
        # empty needs and any external-singleton grouped first
        if need_tpl == ():
            return (0, )
        if len(need_tpl) == 1:
            var = need_tpl[0]
            # external dependency → treat like empty
            if var not in var_to_producer_line:
                return (0, var)
            # otherwise sort by producer line
            return (1, var_to_producer_line[var])
        # multi‐var: after singletons, by size then lex
        return (2, len(need_tpl), need_tpl)

    distinct.sort(key=needs_key)

    # 6) Build lookup of need‐tpl → group‐index
    needtpl_to_groupidx = {tpl: idx for idx, tpl in enumerate(distinct)}

    # 7) Compute wait index for each tpl
    def compute_wait_index(tpl):
        if tpl == () or (len(tpl)==1 and tpl[0] not in var_to_producer_line):
            return None
        # find group of each var’s producer
        idxs = []
        for v in tpl:
            if v in var_to_producer_line:
                prod_line = var_to_producer_line[v]
                prod_needs = needs_map[prod_line]
                idxs.append(needtpl_to_groupidx[prod_needs])
        return max(idxs) if idxs else None

    # 8) Format the result
    result: List[List[str]] = []
    for tpl in distinct:
        wait_idx = compute_wait_index(tpl)
        grp = []
        for s in sorted(buckets[tpl], key=lambda x: x["code line"]):
            stmt = s["statement"]
            dep_str = ", ".join(tpl) if tpl else "none"
            wi = str(wait_idx) if wait_idx is not None else "none"
            grp.append(f"{stmt} : {dep_str} : {wi}")
        result.append(grp)

    return result
def check_syntax_errors(file_path,error_file="errors.txt"):
    try:
        py_compile.compile(file_path, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"Syntax error in {file_path}: {e.msg}")
        with open(error_file, 'a') as ef:
            ef.write(f"Syntax error in {file_path}: {e.msg}\n")
        return False
    
def build_ddg(file_path):
    try:
        with open(file_path, 'r') as f:
            code = f.read()

        # Remove all content between any two "#---------------------------------------------------------------------------------------------------------"   
        code = re.sub(
            r"#-+\n.*?\n#-+\n",
            "",
            code,
            flags=re.DOTALL
        )

        tree = ast.parse(code)
        graph=DDG_Wrapper(tree)
        graph.build_ddgs()
        return graph
    except Exception as e:
        print(f"Error building DDG for {file_path}: {e}")
        return None
def dependency_analyzer(folder):
    jsons = sorted(glob.glob(f"{folder}/*.json"))

    if len(jsons) % 2 != 0:
        raise ValueError("Expected an even number of JSON files (pairs of edges and nodes).")

    for i in range(0, len(jsons), 2):
        with open(jsons[i], 'r') as f1, open(jsons[i + 1], 'r') as f2:
            edges = json.load(f1)
            nodes = json.load(f2)

        print(f"\nProcessing pair: {os.path.basename(jsons[i])}, {os.path.basename(jsons[i+1])}")
        result = group_by_needs_with_wait_index(nodes, edges)
        print(result)


def main():
    error_file = "errors.txt"
    if len(sys.argv) < 2:
        print("Usage: python Parallelizer .py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    
    #! Check for syntax errors
    if check_syntax_errors(filename, error_file):
       print(f"1. Syntax check passed for {filename}.")
    
    graph = build_ddg(filename)
    if graph:
        print(f"2. DDG built successfully for {filename}.")
        graph.visualize_graph_data()
        graph.save_to_json('temp')
        functions = graph.parser.functions
    else:
        print(f"2. Failed to build DDG for {filename}. Check {error_file} for details.")   
    
    dependency_analyzer('temp')
    

if __name__ == "__main__":
    main()

    
