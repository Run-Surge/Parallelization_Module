# How to Use This for Any Loop
# Matrix Multiplication? Just change operation = "C[i0, i1] = sum(A[i0, k] * B[k, i1])".
# Higher Dimensions? Add more (start, end) tuples in loop_bounds.
# Want GPU Execution? Modify lp.generate_code(knl, target=lp.CTarget()) to lp.generate_code(knl, target=lp.OpenCLTarget()).
import loopy as lp
import numpy as np


def optimize_loops(loop_bounds, operation):
    """
    Optimizes and executes a loop using Loopy.

    Args:
        loop_bounds (list of tuples): List of (start, end) for each loop dimension.
        operation (str): Loopy operation as a string (e.g., "C[i,j] = A[i,j] + B[i,j]").

    Returns:
        None (prints the generated optimized code).
    """
    # Generate index variables dynamically
    indices = ",".join(f"i{idx}" for idx in range(len(loop_bounds)))

    # Generate domain constraints dynamically
    constraints = " and ".join(
        f"0 <= i{idx} < {end}" for idx, (start, end) in enumerate(loop_bounds)
    )

    # Create Loopy kernel
    knl = lp.make_kernel(
        f"{{[{indices}]: {constraints}}}", operation  # Domain  # Operation
    )

    # Apply loop optimizations
    for idx in range(len(loop_bounds)):
        knl = lp.tile_loop(
            knl, f"i{idx}", 2
        )  # Tile each loop level (adjust tile size as needed)

    knl = lp.prioritize_loops(
        knl, indices[::-1]
    )  # Prioritize inner loops for better memory access

    # Generate optimized code
    code, _ = lp.generate_code(knl)
    print("\nOptimized Code:\n", code)


# Example: Optimizing a 2D loop that adds two matrices
loop_bounds = [(0, 4), (0, 4)]  # 4x4 matrix
operation = "C[i0, i1] = A[i0, i1] + B[i0, i1]"

optimize_loops(loop_bounds, operation)
