from Memory_Estimator import *
from DDG import *
import py_compile
import sys







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
        tree = ast.parse(open(file_path).read())
        graph=DDG_Wrapper(tree)
        graph.build_ddgs()
        return graph
    except Exception as e:
        print(f"Error building DDG for {file_path}: {e}")
        return None

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
    else:
        print(f"2. Failed to build DDG for {filename}. Check {error_file} for details.")   
    

if __name__ == "__main__":
    main()

    
