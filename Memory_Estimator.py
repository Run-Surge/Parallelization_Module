import ast
import json
import sys
import math
import enum
import os

class Primitives_Estimator:
    def __init__(self):
        pass
    def estimate_primitive_size(self, value):
        '''
        Estimate the size of a primitive value in bytes.
        '''
        return sys.getsizeof(value)
    def estimate_list_size(self,length):
        '''
        Estimate the size of a list in bytes based on its length.
        the size is calculated based on the number of elements and a precomputed capacity.
        size = size of #pointers ceiled
        '''
        def get_precomputed_capacity(length):
            if length == 0:
                return 0
            elif length <= 4:
                return 4
            elif length <= 8:
                return 8
            elif length <= 16:
                return 16
            elif length <= 25:
                return 25
            elif length <= 35:
                return 35
            elif length <= 49:
                return 49
            elif length <= 64:
                return 64
            else:
                return int(length * 1.025)
        base_size = sys.getsizeof([]) + 8 * get_precomputed_capacity(length)
        return base_size
class VariableToConstantTransformer(ast.NodeTransformer):
    def visit_Name(self, node):
        return ast.Constant(value=f"${node.id}")
class ConstantListToNamesTransformer(ast.NodeTransformer):
    def visit_Constant(self, node):
        # Only process string constants like "$var"
        if isinstance(node.value, str) and node.value.startswith("$"):
            return ast.Name(id=node.value[1:], ctx=ast.Load())

        # Handle Constant that wraps a list of strings like ["$x", "$y"]
        if isinstance(node.value, list):
            # Convert list elements recursively if they start with $
            elements = []
            for item in node.value:
                if isinstance(item, str) and item.startswith("$"):
                    elements.append(ast.Name(id=item[1:], ctx=ast.Load()))
                else:
                    elements.append(ast.Constant(value=item))
            return ast.List(elts=elements, ctx=ast.Load())

        return node

class AugAssignToExtend(ast.NodeTransformer):
    def visit_AugAssign(self, node):
        if isinstance(node.op, ast.Add):
            return ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.copy_location(
                            ast.Name(id=node.target.id, ctx=ast.Load()),
                            node.target
                        ),
                        attr='extend',
                        ctx=ast.Load()
                    ),
                    args=[node.value],
                    keywords=[]
                )
            )
        return node
class InsertToAppend(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)  # Visit children nodes first
        if (
            isinstance(node.func, ast.Attribute) and
            node.func.attr == 'insert' and
            len(node.args) == 2
        ):
            # Change method name to 'append'
            node.func.attr = 'append'
            # Keep only the second argument (the value to insert)
            node.args = [node.args[1]]
        return node
class Memory_Parser:
    transformer = VariableToConstantTransformer()
    transformer2 = ConstantListToNamesTransformer()
    transformer3 = AugAssignToExtend()
    transformer4 = InsertToAppend()
    class AssignTypes(enum.Enum):
        PRIMITIVE = "primitive"
        LIST = "list" 
    def __init__(self):
        self.primitives_estimator = Primitives_Estimator()
        self.vars = {}  #! varibles parsed so far (name: (value, memory, type))
        self.funcs = {'int':('int',0), 'str':('str',0), 'float':('float',0), 'bool':('bool',0), 'bytes':('bytes',0), 'bytearray':('bytearray',0), 'complex':('complex',0)
                      ,'list':('list',0)}  #! functions parsed so far (name: (type, memory))
        self.primitives=['int','str','float','bool','bytes','bytearray','complex','unk']  #! primitive types  
    def _reset(self):
        '''
        resets the memory parser.
        '''
        self.vars = {}
    def _hande_primitives_type_conversions(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'int':  
                arg_val = self._evaluate_primtive_expression(node.args[0])
                return int(arg_val)
        elif isinstance(node.func, ast.Name) and node.func.id == 'str':
            return str(self._evaluate_primtive_expression(node.args[0]))
        elif isinstance(node.func, ast.Name) and node.func.id == 'float':
            return float(self._evaluate_primtive_expression(node.args[0]))
        return None
    def _handle_mathematical_ops(self, node, left_val, right_val):
        if isinstance(node.op, ast.Add):
            return left_val + right_val
        elif isinstance(node.op, ast.Sub):
            return left_val - right_val
        elif isinstance(node.op, ast.Mult):
            return left_val * right_val
        elif isinstance(node.op, ast.Div):
            return left_val / right_val
        elif isinstance(node.op, ast.Pow):
            return left_val ** right_val
        elif isinstance(node.op, ast.Mod):
            return left_val % right_val
        else:
            raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
        
    def _evaluate_primtive_expression(self, node):
        if isinstance(node, ast.Constant):  
            return node.value
        elif isinstance(node, ast.BinOp):  
            left_val = self._evaluate_primtive_expression(node.left)
            right_val = self. _evaluate_primtive_expression(node.right)
            result = self._handle_mathematical_ops(node, left_val, right_val)
            if result is not None:
                return result    
        elif isinstance(node, ast.Name):  
                if node.id in self.vars:
                    return self.vars[node.id][0]  
                else:
                    raise NameError(f"Variable '{node.id}' is not defined.")
        elif isinstance(node, ast.Call): 
            result = self._hande_primitives_type_conversions(node)
            if result is not None:
                return result
        else:
            raise TypeError(f"Unsupported AST node: {type(node).__name__}")   
           
    def _evaluate_primitive_assignment(self,stmt):
        '''
        
        evaluate primitive assignment statements.
        
        '''
        var_name = stmt.targets[0].id  
        result = self._evaluate_primtive_expression(stmt.value)
        memory = self.primitives_estimator.estimate_primitive_size(result)
        self.vars[var_name] = (result, memory, type(result).__name__) 
    def _assignment_type(self, node):
        '''
        
        Determine the type of assignment based on the AST node.
        supported types are primitive and list, primitive functions.
        
        '''
        if isinstance(node, ast.Constant):  
            if type(node.value).__name__ in self.primitives: 
                return self.AssignTypes.PRIMITIVE
            else:
                return self.AssignTypes.LIST
        elif isinstance(node, ast.List) or isinstance(node, ast.ListComp):
            return self.AssignTypes.LIST
        elif isinstance(node, ast.Name):
            if self.vars[node.id][2] in self.primitives:
                return self.AssignTypes.PRIMITIVE
            elif self.vars[node.id][2] == 'list':
                return self.AssignTypes.LIST
        elif isinstance(node, ast.Subscript):
            return self.AssignTypes.LIST  # Subscript is typically used for list indexing
        elif isinstance(node, ast.Call):
            if self.funcs[node.func.id][0] in self.primitives:
                return self.AssignTypes.PRIMITIVE
            elif self.funcs[node.func.id][0] == 'list':
                return self.AssignTypes.LIST 
        elif isinstance(node, ast.BinOp):
            left_type = self._assignment_type(node.left)
            right_type = self._assignment_type(node.right)
            if left_type == self.AssignTypes.LIST or right_type == self.AssignTypes.LIST:
                return self.AssignTypes.LIST
            elif left_type == self.AssignTypes.PRIMITIVE and right_type == self.AssignTypes.PRIMITIVE:
                return self.AssignTypes.PRIMITIVE
    def _evaluate_list_assignment(self, stmt,first=True):
        '''
        
        gets size of a list assignment statement.
        
        '''
        def _parse_list_elements_sizes(node):
            if isinstance(node, ast.List):  
                sizes = [_parse_list_elements_sizes(el) for el in node.elts]
                total_size = sum([size for size in sizes])
                total_length = len(node.elts)
                return total_size + self.primitives_estimator.estimate_list_size(total_length)                     
            elif isinstance(node,ast.Constant):
                return sys.getsizeof(node.value)
            elif isinstance(node, ast.Name):
                if node.id in self.vars:
                    return self.vars[node.id][1]            
        var = stmt.targets[0].id
        multiplier = 1
        if (isinstance(stmt.value, ast.Call)):
            stmt=stmt.value.args[0]
        elif (isinstance(stmt.value, ast.Subscript)):
            target = stmt.value.value.id
            if target not in self.vars:
                raise NameError(f"Variable '{target}' is not defined syntax error.")
            if self.vars[target][2] != 'list':
                raise TypeError(f"Variable '{target}' is not a list syntax error.")
            total_size = self.vars[target][1]
            total_length = self.vars[target][0]
            slice = stmt.value.slice
            lower = None
            upper = None
            step = None
            if isinstance(slice, ast.Slice):
                lower = slice.lower.value if isinstance(slice.lower, ast.Constant) else None
                upper = slice.upper.value if isinstance(slice.upper, ast.Constant) else None
                step = slice.step.value if isinstance(slice.step, ast.Constant) else 1
            elif isinstance(slice, ast.Constant):
                lower = slice.value
                upper = None
                step = None
            length = 0
            size = 0
            if lower is not None and upper is not None:
                length = (upper - lower) // step
                size = total_size/total_length * length + sys.getsizeof([])
                self.vars[var] = (length, size, 'list')  
            elif lower is not None and  upper is None:
                if isinstance(slice, ast.Slice):
                    length = (total_length - lower)// step
                    size = (total_size // total_length) * length + sys.getsizeof([])
                    self.vars[var] = (length, size, 'list')
                else:
                    size = total_size//total_length 
                    self.vars[var] = ('1', size, 'list') #! assumed to be a list 
                    #! Note: this is an over estimation as it takes the size of the pointer into account 
            elif lower is None and upper is not None:
                length = upper// step
                size = total_size//total_length * length + sys.getsizeof([])
                self.vars[var] = (length, size, 'list')
            return  
                        
        elif (isinstance(stmt.value, ast.BinOp)): #! handle list multiplication
            op = stmt.value.op
            if isinstance(op, ast.Mult):
                left = stmt.value.left
                right = stmt.value.right
                multiplier = right.value if  isinstance(left, ast.List) else left.value
                list_val=left if isinstance(left, ast.List) else right
                stmt=list_val
            elif isinstance(op, ast.Add):
                left = stmt.value.left
                right = stmt.value.right
                left_size = _parse_list_elements_sizes(left)
                right_size = _parse_list_elements_sizes(right)
                total_size = left_size + right_size
                total_length = 0
                if isinstance(left, ast.Name) and left.id in self.vars:
                    if self.vars[left.id][2] != 'list':
                        raise TypeError(f"Variable '{left.id}' is not a list synax error.")
                    total_length += self.vars[left.id][0]
                    total_size+=self.primitives_estimator.estimate_list_size(self.vars[left.id][0]) - sys.getsizeof([]) 
                elif isinstance(left, ast.List):
                    total_length += len(left.elts)
                if isinstance(right, ast.Name) and right.id in self.vars:
                    if self.vars[right.id][2] != 'list':
                        raise TypeError(f"Variable '{right.id}' is not a list synax error.")
                    total_length += self.vars[right.id][0]
                    total_size+=self.primitives_estimator.estimate_list_size(self.vars[right.id][0]) 
                    
                elif isinstance(right, ast.List):
                    total_length += len(right.elts)
                self.vars[var] = (total_length, total_size, 'list')               
                return
        elif (isinstance(stmt.value, ast.ListComp)):
            elt = stmt.value.elt
            new_assign = ast.Assign(
                targets=[ast.Name(id=var, ctx=ast.Store())],
                value=elt
            )
            multiplier = (
                stmt.value.generators[0].iter.args[0].value
                if isinstance(stmt.value.generators[0].iter, ast.Call)
                and isinstance(stmt.value.generators[0].iter.args[0], ast.Constant)
                else 1
            )            
            self._evaluate_list_assignment(new_assign)
            length = self.vars[var][0] * multiplier
            size = self.vars[var][1] * multiplier
            self.vars[var] = (length, size, 'list')
            return
        else:
            stmt=stmt.value
        list_length = len(stmt.elts)
        memory = self.primitives_estimator.estimate_list_size(list_length)
        elements_size = _parse_list_elements_sizes(stmt) * multiplier
        list_length = list_length * multiplier
        if first:
           self.vars[var] = (list_length,elements_size,'list')
        else:
            self.vars[var] = (self.vars[var][0] + list_length, self.vars[var][1] + elements_size, 'list')
        
          
    def _assignmemt_handler(self,tree):
        stmt = tree
        if self._assignment_type(stmt.value) == self.AssignTypes.PRIMITIVE:
            self._evaluate_primitive_assignment(stmt)
        elif self._assignment_type(stmt.value) == self.AssignTypes.LIST :
            print("List Assignment")            
            self._evaluate_list_assignment(stmt)
    def _handle_list_insertion(self, var,func,args,in_loop = 1):
        if func == 'append':
            #! start with $ then a variable name
            if isinstance(args[0], str) and args[0].startswith("$"):
               args[0] = args[0][1:]  # Remove the leading '$'
               if args[0] not in self.vars:
                   raise NameError(f"Variable '{args[0]}' is not defined syntax error.")
               args[0] = self.vars[args[0]][0]  # Get the value of the variable
            for i in range(in_loop):
                new_node = ast.Assign(
                    targets=[ast.Name(id=var, ctx=ast.Store())],
                    value=ast.List(elts=[ast.Constant(value=args[0])], ctx=ast.Load())
                )
                new_node = self.transformer2.visit(new_node)
                # print(f"New Node: {ast.dump(new_node)}")
                self._evaluate_list_assignment(new_node, False)
        elif func == 'extend':  
            #! extend treats immutable objects as if they were re-created in memory together with their pointers.
            
            flattened_args = []
            for sublist in args:
                for item in sublist:
                    if isinstance(item, str) and item.startswith("$"):
                        item = item[1:]
                        if item not in self.vars:
                            raise NameError(f"Variable '{item}' is not defined syntax error.")
                        if self.vars[item][2] == 'list':
                            length = self.vars[item][0]
                            size = self.vars[item][1]
                            total_size = size + self.primitives_estimator.estimate_list_size(length) -  sys.getsizeof([]) #! should be 2 one for get the size of the list and one for the pointer in the original list
                            self.vars[var] = (self.vars[var][0] + length, self.vars[var][1] + total_size, 'list')
                            continue
                    flattened_args.append(item)
            args = flattened_args
            for i in range(in_loop):
                for arg in args:
                    new_node = ast.Assign(
                        targets=[ast.Name(id=var, ctx=ast.Store())],
                        value=ast.List(elts=[ast.Constant(value=arg)], ctx=ast.Load())
                    )
                    new_node = self.transformer2.visit(new_node)
                    # print(f"New Node: {ast.dump(new_node)}")
                    self._evaluate_list_assignment(new_node, False)
    def _insertion_handler(self, tree,in_loop = 1):
        def extract_call_info(tree):
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_node = node.func
                    if isinstance(func_node, ast.Attribute):
                        var_id = func_node.value.id  # e.g., 'x'
                        func_type = func_node.attr   # e.g., 'append'
                        args = []
                        for arg in node.args:
                            if isinstance(arg, ast.Name):
                                # Capture variable name as a string
                               args.append([f"${arg.id}"])
                            else:
                                node = self.transformer.visit(node)
                                try:
                                    args.append(ast.literal_eval(arg))
                                except (ValueError, SyntaxError):
                                    raise ValueError(f"Unsupported argument type: {type(arg).__name__}")
                        return var_id, func_type, args
         
        if isinstance(tree, ast.AugAssign): #! for handling +=
            tree = self.transformer3.visit(tree)
        else: #1 to replace insert with append
            contains_insert = any(
                isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                node.func.attr == 'insert'
                for node in ast.walk(tree)
            )
            if contains_insert:
                tree = self.transformer4.visit(tree)
        var, func_type, args = extract_call_info(tree)
        if not var in self.vars:
            raise NameError(f"Variable '{var}' is not defined syntax error.")
        if self.vars[var][2] == 'list':
           self._handle_list_insertion(var, func_type,args, in_loop)   
            
        
    def _handle_list_deletion(self, var, func_type,in_loop = 1):
        if func_type == 'pop':
            if self.vars[var][0] == 0:
                raise IndexError(f"pop from empty list syntax error.")
            for i in range(in_loop):
                total_size = self.vars[var][1]
                total_length = self.vars[var][0]
                new_size = total_size - (total_size // total_length)  
                self.vars[var] = (total_length - 1, new_size, 'list')
            return
        elif func_type == 'clear':
            self.vars[var] = (0, sys.getsizeof([]), 'list')  # Reset to empty list
        elif func_type == 'remove':
            for i in range(in_loop):
                new_length = self.vars[var][0] - 1
                new_size = self.vars[var][1] - (self.vars[var][1] // self.vars[var][0])
                self.vars[var] = (new_length, new_size, 'list') 
    def _deletion_handler(self, tree, in_loop = 1):
        def extract_call_info(tree):
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_node = node.func
                    if isinstance(func_node, ast.Attribute):
                        var_id = func_node.value.id  # e.g., 'x'
                        func_type = func_node.attr   # e.g., 'pop'
                        return var_id, func_type
        var_id, func_type = None, None
        if  isinstance(tree.body[0], ast.Delete): #! handle del statements
            stmt = tree.body[0]
            subscript = stmt.targets[0]
            var_id = subscript.value.id
            slice = subscript.slice
            lower = None
            upper = None
            step = None
            if isinstance(slice, ast.Slice):
                lower = slice.lower.value if isinstance(slice.lower, ast.Constant) else None
                upper = slice.upper.value if isinstance(slice.upper, ast.Constant) else None
                step = slice.step.value if isinstance(slice.step, ast.Constant) else 1
            elif isinstance(slice, ast.Constant):
                lower = slice.value
                upper = None
                step = None
            total_length = self.vars[var_id][0]
            total_size = self.vars[var_id][1]
            if lower is not None and upper is not None:
                length = (upper - lower) // step
                size = total_size / total_length * length
                self.vars[var_id] = (total_length - length, total_size - size, 'list')
            elif lower is not None:
                length = total_length - 1
                size = total_size - total_size // total_length
                self.vars[var_id] = (length, size, 'list')
                
            return                
        else:
            var_id, func_type = extract_call_info(tree)
        if var_id not in self.vars:
            raise NameError(f"Variable '{var_id}' is not defined syntax error.")
        if self.vars[var_id][2] != 'list':
            raise TypeError(f"Variable '{var_id}' is not a list syntax error.")
        self._handle_list_deletion(var_id, func_type, in_loop)
                    
         
    def _list_method_handler(self, tree):
        def extract_call_info(tree):
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_node = node.func
                    if isinstance(func_node, ast.Attribute):
                        var_id = func_node.value.id  # e.g., 'x'
                        func_type = func_node.attr   # e.g., 'pop'
                        return var_id, func_type
        var, func_type = extract_call_info(tree)
        #! returns length,size
        if func_type == ['reverse','sort']:
            if var not in self.vars:
                raise NameError(f"Variable '{var}' is not defined syntax error.")
            if self.vars[var][2] != 'list':
                raise TypeError(f"Variable '{var}' is not a list syntax error.")
            # Reversing a list does not change its size or length
            return None,None
        elif func_type in ['count','index']:
            return 0, sys.getsizeof(10000000)  #! hardcoded maybe changed later (or maybe not :( )
        elif func_type in ['copy']:
            return self.vars[var][0],self.vars[var][1]
            
        
    
        # print(f"Variable ID: {var}, Function Type: {func_type}, Arguments: {args}")
    def _file_handler(self, tree):
        '''
        gets the file metadata and records it in the dictionary.
        '''
        def extract_file_info(tree):
            file_path = None
            list_name = None

            for node in ast.walk(tree):
                # Find open() call and extract file path
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'open':
                    if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                        file_path = node.args[0].value

                # Find assignment to variable from file.readlines()
                if isinstance(node, ast.Assign):
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                        if node.value.func.attr == 'readlines' and isinstance(node.targets[0], ast.Name):
                            list_name = node.targets[0].id

            return file_path, list_name
        file_path ,var = extract_file_info(tree)
        file_size = os.path.getsize(file_path) + sys.getsizeof([])  #! add the size of the list pointer
        length = 0
        with open(file_path, 'rb') as f:
            length = sum(1 for _ in f)
        self.vars[var] = (length, file_size, 'list')
    def _get_return_size_length(self,node):
        var_name = None
        lower = None
        upper = None
        step = None
        ret_stmt = node.body[0]
        if not isinstance(ret_stmt, ast.Return):
            return None

        value = ret_stmt.value
   
        if isinstance(value, ast.Name):
            var_name = value.id

        # Case: return x[0] or return x[0:4] or return x[0:8:2]
        if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
            var_name = value.value.id

            # Case: return x[0]
            if isinstance(value.slice, ast.Constant):
                lower = value.slice.value
                upper = lower + 1
                step = 1
    
            # Case: return x[0:4] or x[0:8:2]
            elif isinstance(value.slice, ast.Slice):
                def get_val(val): return val.value if isinstance(val, ast.Constant) else None
                lower = get_val(value.slice.lower)
                upper = get_val(value.slice.upper)
                step = get_val(value.slice.step) if get_val(value.slice.step) is not None else 1
            
        if var_name not in self.vars:
            raise NameError(f"Variable '{var_name}' is not defined syntax error.")
        original_length, original_size, _ = self.vars[var_name]
        if lower is None:
            length = self.vars[var_name][0] if self.vars[var_name][2] == 'list' else 1
            return original_size, length
        else:
            new_length = (upper - lower) // step
            new_size = int(original_size / original_length * new_length)
            return new_size, new_length
            
        