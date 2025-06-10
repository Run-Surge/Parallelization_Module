from Memory_Estimator import *
from DDG import *
import py_compile
import sys
from collections import defaultdict, deque
from typing import List, Dict, Any
import glob
import json
import copy

from collections import defaultdict
from typing import List, Dict, Any

def group_by_needs_with_wait_index(
    statements: List[Dict[str, Any]],
    dependency_graph: Dict[str, Any]
) -> Dict[tuple, List[str]]:
    
    def get_dependency_dict(statements):
        line_to_stmt = {stmt["code line"]: stmt["statement"] for stmt in statements}
        grouped_statements = defaultdict(list)
        first_no_dependency_handled = False

        for stmt in statements:
            line_num = stmt["code line"]
            line_str = str(line_num)
            info = dependency_graph.get(line_str, {})
            depends_on = info.get("Depends on", [])

            if not depends_on:
                key = ("none:none",)
                first_no_dependency_handled = True
                grouped_statements[key].append(line_to_stmt[line_num])
            else:
                key_parts = [f"{dep['Dependency'][0]}:{dep['Node']}" for dep in depends_on]
                key = tuple(sorted(key_parts))
                grouped_statements[key].append(line_to_stmt[line_num])

        # Convert to list of dicts
        result = [{"key": key, "statements": stmts} for key, stmts in grouped_statements.items()]
        return result  
    def get_line_to_statement_map(statements: List[Dict[str, Any]]) -> Dict[int, str]:
        return {stmt["code line"]: stmt["statement"] for stmt in statements}
    def convert_keys_to_dict_indices(grouped_list, line_to_code_mapping):
        def get_statement_index(grouped_list,code):
            for i, item in enumerate(grouped_list):
                if code in item["statements"]:
                    return i
            return None
        for ind,dictionnary in enumerate(grouped_list):
            keys = dictionnary["key"]
            keys = list(keys)
            new_keys = []
            for key in keys:
                lineno = key.split(":")
                if lineno[1] == "none":
                    continue
                code_line = line_to_code_mapping.get(int(lineno[1]), None)
                index = get_statement_index(grouped_list, code_line)
                new_key = f'{lineno[0]}:{index}'
                new_keys.append(new_key) 
            new_key_tuple = tuple(new_keys)
            grouped_list[ind]["key"] = new_key_tuple
        return grouped_list
    result = get_dependency_dict(statements)
    print(result)
    line_to_code_mapping = get_line_to_statement_map(statements)
    result = convert_keys_to_dict_indices(result,  line_to_code_mapping)
    
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
    results = []
    if len(jsons) % 2 != 0:
        raise ValueError("Expected an even number of JSON files (pairs of edges and nodes).")
    for i in range(0, len(jsons), 2):
        with open(jsons[i], 'r') as f1, open(jsons[i + 1], 'r') as f2:
            edges = json.load(f1)
            nodes = json.load(f2)

        print(f"\nProcessing pair: {os.path.basename(jsons[i])}, {os.path.basename(jsons[i+1])}")
        result = group_by_needs_with_wait_index(nodes, edges)
        # print(result)
        for x in result:
            print(f"Key: {x['key']}, Statements: {x['statements']}")
        results.append(result)
    return results

def get_memory_foortprint(file_path, entry_point, functions):
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
    def get_func_footprint(func_name, args, functions, func_lines_footprint, global_parser):
        def find_func_index(func_name, func_list):
            for idx, func_tuple in enumerate(func_list):
                if func_tuple[0] == func_name:
                    return idx
            return -1
        def get_footprint(node,local_parser,func_lines_footprint):
            tree = copy.deepcopy(node)
            if isinstance(tree, ast.Assign):
                local_parser._assignmemt_handler(tree)
            elif  isinstance(tree, ast.AugAssign):
                local_parser._insertion_handler(tree)
            elif isinstance(tree, ast.Expr):
                func = tree.value.func.attr 
                if func in ['insert', 'append', 'extend']:
                    local_parser._insertion_handler(tree)
                elif func in ['pop', 'remove','clear']:
                    local_parser._deletion_handler(tree)
            elif  isinstance(tree, ast.Delete):
                local_parser._deletion_handler(tree.body[0])
            print(ast.unparse(node))  # Debugging: print the source code of the node
            func_lines_footprint[func_name][ast.unparse(node)] = sum(val[1] for val in local_parser.vars.values())
        local_parser = Memory_Parser()
        lines_footprint = {}
        index = find_func_index(func_name, functions)
        if index != -1:
            fargs = functions[index][1]
            if len(args) != len(fargs):
                raise ValueError(f"Function {func_name} called with incorrect number of arguments.")
            else:
                for i, arg in enumerate(args):
                    local_parser.vars[fargs[i]] = global_parser.vars[arg]
            code = functions[index][2]
            func_def = f"def {func_name}({', '.join(fargs)}):"
            args_total_memory = sum(val[1] for val in local_parser.vars.values())
            func_lines_footprint[func_name][func_def] = args_total_memory 
            tree = ast.parse(code)
            for node in tree.body:
                # print(ast.dump(node, indent=4))  # Debugging: print the AST nodes
                get_footprint(node, local_parser, func_lines_footprint)
                print(func_lines_footprint)
                # print(local_parser.vars)
        else:
            raise ValueError(f"Function {func_name} not found in the provided functions list.")
            
    def get_main_footprint(entry_point, functions,global_parser):
        def get_func_attributes(node, functions):
            func = value.func
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr
            args = []
            for arg in value.args:
                if isinstance(arg, ast.Name):
                    args.append(arg.id)
                elif isinstance(arg, ast.Constant):
                    args.append(arg.value)
                else:
                    args.append(ast.dump(arg))  # fallback for complex args

            return func_name, args
           
        tree = ast.parse(entry_point)
        main_lines_footprint = {}
        func_lines_footprint = defaultdict(dict)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
                value = node.value
                if isinstance(value, ast.Call):
                    func_name, args = get_func_attributes(node, functions)
                    return_footprint = get_func_footprint(func_name, args, functions,func_lines_footprint,global_parser)
                    
                    
                        
            
                
    memory_parser = Memory_Parser()
    tree = ast.parse(open(file_path, 'r').read())
    file_name = get_file_name(tree)
    read_file_block = get_read_file_block(tree)
    read_file_block = read_file_block.replace("FILE_NAME", f"'{file_name}'")
    read_file_ast = ast.parse(read_file_block)
    memory_parser._file_handler(read_file_ast)
    memory_parser.vars['data'] = memory_parser.vars['lines']
    del memory_parser.vars['lines']  
    get_main_footprint(entry_point, functions, memory_parser)
    # print(memory_parser.vars)
def main():
    error_file = "errors.txt"
    if len(sys.argv) < 2:
        print("Usage: python Parallelizer .py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    filename= 'sample_submission.py'
    #! Check for syntax errors
    if check_syntax_errors(filename, error_file):
       print(f"1. Syntax check passed for {filename}.")
    
    graph = build_ddg(filename)
    if graph:
        print(f"2. DDG built successfully for {filename}.")
        # graph.visualize_graph_data()
        graph.save_to_json('temp')
        functions = graph.parser.functions
        entry_point= graph.parser.entry_point
    else:
        print(f"2. Failed to build DDG for {filename}. Check {error_file} for details.")   
    
    dep_2d_list = dependency_analyzer('temp')
    if dep_2d_list:
        print(f"3. Dependency analysis completed for {filename}.")
    
    # get_memory_foortprint(filename,entry_point,functions)
        
    

if __name__ == "__main__":
    main()
