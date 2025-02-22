import numpy as np
import time
import psutil
from numba import njit, prange
import os

# Define matrix size
N = 512
A = np.random.rand(N, N)
B = np.random.rand(N, N)


# Function to measure execution time, CPU usage, and memory usage
def benchmark(func, *args):
    process = psutil.Process()
    start_mem = process.memory_info().rss / 1e6  # Memory in MB
    start_time = time.time()

    result = func(*args)  # Run the function

    end_time = time.time()
    end_mem = process.memory_info().rss / 1e6  # Memory in MB
    cpu_usage = process.cpu_percent(interval=0.1)  # Measure CPU %

    runtime = end_time - start_time
    mem_used = end_mem - start_mem

    output = (
        f"{func.__name__}:\n"
        f"   Execution Time: {runtime:.4f} sec\n"
        f"   Memory Used: {mem_used:.2f} MB\n"
        f"   CPU Usage: {cpu_usage:.2f}%\n\n"
    )

    print(output)

    # Save to results file
    with open("results.txt", "a") as f:
        f.write(output)

    return result


# Pure Python Loop
def matmul_python(A, B):
    N = A.shape[0]
    C = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            for k in range(N):
                C[i, j] += A[i, k] * B[k, j]
    return C


# NumPy dot (Highly Optimized)
def matmul_numpy(A, B):
    return np.dot(A, B)


# Numba Parallelized Loop
@njit(parallel=True)
def matmul_numba(A, B):
    N = A.shape[0]
    C = np.zeros((N, N))
    for i in prange(N):
        for j in range(N):
            for k in range(N):
                C[i, j] += A[i, k] * B[k, j]
    return C


# Cython (If Available)
try:
    from matmul import matmul_cython

    cython_available = True
except ImportError:
    cython_available = False

# Clear previous results file
if os.path.exists("results.txt"):
    os.remove("results.txt")

# Run Benchmarks
benchmark(matmul_python, A, B)
benchmark(matmul_numpy, A, B)
benchmark(matmul_numba, A, B)

if cython_available:
    benchmark(matmul_cython, A, B)
else:
    print(
        " Cython version not compiled. Run `cythonize -a -i matmul.pyx` to compile it.\n"
    )
