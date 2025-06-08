from Memory_Estimator import *
from DDG import *
import py_compile
import sys
from collections import defaultdict, deque
from typing import List, Dict, Any
import glob
import json


from collections import defaultdict
from typing import List, Dict, Any

def group_by_needs_with_wait_index(
    statements: List[Dict[str, Any]],
    dependency_graph: Dict[str, Any]
) -> List[List[str]]:
    # 1) Map code_line → produced variables
    produced = {s["code line"]: s["has"] for s in statements}

    # 2) Build needs_map: code_line → sorted tuple of needed vars
    needs_map = {
        s["code line"]: tuple(sorted(s["needs"]))
        for s in statements
    }

    # 3) Bucket statements by needs‐tuple
    buckets = defaultdict(list)
    for s in statements:
        tpl = needs_map[s["code line"]]
        buckets[tpl].append(s)

    # 4) Sort distinct needs‐tuples for grouping
    distinct = list(buckets.keys())
    # def needs_key(tpl):
    #     if not tpl:
    #         return (0,)
    #     if len(tpl) == 1:
    #         var = tpl[0]
    #         # if external, sort by var name
    #         if str(var) not in produced:
    #             return (0, var)
    #         # otherwise by latest producer line
    #         return (1, produced.get(var, 0))
    #     return (2, len(tpl), tpl)
    # distinct.sort(key=needs_key)

    # 5) Build lookup: needs‐tpl → group index
    tpl_to_groupidx = {tpl: idx for idx, tpl in enumerate(distinct)}

    # 6) Precompute, for each stmt_line, a var→producer_line from dependency_graph
    #    dependency_graph keys are strings
    dep_map: Dict[int, Dict[str,int]] = {}
    for k, info in dependency_graph.items():
        stmt_line = int(k)
        dep_map[stmt_line] = {}
        for dep in info.get("Depends on", []):
            prod_line = dep["Node"]
            for var in dep["Dependency"]:
                dep_map[stmt_line][var] = prod_line

    # 7) Format each group, using dep_map to find wait‐indices
    result: List[List[str]] = []
    latest_group_idx = {}  # Track the latest group index for each variable

    for group_idx, tpl in enumerate(distinct):
        grp = []
        temp_latest_group_idx = latest_group_idx.copy()  # Temporary copy for calculating wait indices
        for s in sorted(buckets[tpl], key=lambda x: x["code line"]):
            stmt_line = s["code line"]
            waits = []
            for var in tpl:
                prod_line = dep_map.get(stmt_line, {}).get(var)
                if prod_line is None:
                    wait_idx = None
                else:
                    # Use temp_latest_group_idx to find the correct group index
                    wait_idx = temp_latest_group_idx.get(var, None)
                waits.append((var, wait_idx))

            dep_str = ", ".join(tpl) if tpl else "none"
            if waits:
                wait_str = ", ".join(
                    f"{v}:{('none' if idx is None else idx)}"
                    for v, idx in waits
                )
            else:
                wait_str = "none"

            grp.append(f"{s['statement']} : {dep_str} : {wait_str}")
        
        # Update latest_group_idx for variables produced in this group
        for s in buckets[tpl]:
            for var in s["has"]:
                latest_group_idx[var] = group_idx

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
        return result

def get_memory_foortprint(file_path):
    def get_file_name(tree):
        file_name = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'FILE_NAME':
                        if isinstance(node.value, ast.Constant):
                            file_name = node.value.value
        return file_name
    def get_read_file_block(tree):
        try_node = None
        for node in tree.body:
            if isinstance(node, ast.If):
                # match: if __name__ == '__main__':
                test = node.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == '__name__'
                    and any(
                        isinstance(c, ast.Constant) and c.value == '__main__'
                        for c in test.comparators
                    )
                ):
                    # look for the Try in its body
                    for inner in node.body:
                        if isinstance(inner, ast.Try):
                            try_node = inner
                            break

        # 4. Unparse (get source for) that Try node
        if try_node is not None:
            try_src = ast.unparse(try_node)
            return try_src
        else:
            print("No try/except block found under __main__")
                
    memory_parser = Memory_Parser()
    tree = ast.parse(open(file_path, 'r').read())
    # print(ast.dump(tree, indent=4))
    file_name = get_file_name(tree)
    read_file_block = get_read_file_block(tree)
    read_file_block = read_file_block.replace("FILE_NAME", f"'{file_name}'")
    read_file_ast = ast.parse(read_file_block)
    memory_parser._file_handler(read_file_ast)
    print(memory_parser.vars)
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
    
    dep_2d_list = dependency_analyzer('temp')
    if dep_2d_list:
        print(f"3. Dependency analysis completed for {filename}.")
    
    get_memory_foortprint(filename)
        
    

if __name__ == "__main__":
    main()
