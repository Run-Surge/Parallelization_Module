# Parallelization Module 🚀

The **Parallelization Module** is a robust Python toolkit designed to analyze, optimize, and parallelize Python code. It provides functionalities for constructing Data Dependency Graphs (DDGs), estimating memory usage, scheduling splitted python scripts and data, and aggregating results from parallel computations.

---

## 📑 Table of Contents

- [✨ Features](#-features)
  - [Code Analysis & Parallelization](#code-analysis--parallelization)
  - [Memory Estimation](#memory-estimation)
  - [Data Aggregation](#data-aggregation)
  - [Data Generation](#data-generation)
  - [Task Scheduling](#task-scheduling)
- [🛠️ Installation](#installation)
- [🚀 Usage](#-usage)
- [📁 Project Structure](#-project-structure)
- [🐛 Error Handling](#-error-handling)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

### Code Analysis & Parallelization
- **Syntax Validation**: Ensures input code is syntactically correct using `py_compile`, logging errors to `errors.txt`.
- **Data Dependency Graph (DDG) Construction**: Builds DDGs to model data flow and dependencies using Abstract Syntax Tree (AST) parsing in `DDG.py`. Identifies variable definitions (`has`) and usages (`needs`).
- **Dependency Analysis**: Groups statements by dependencies to identify parallelizable code segments, implemented in `Parallelizer.py` (e.g., `group_by_needs_with_wait_index`).

### Memory Estimation
- **Primitive & List Size Calculation**: Estimates memory usage for primitive data types and lists using `sys.getsizeof` and precomputed list capacities in `Memory_Estimator.py`.
- **Variable Memory Tracking**: Dynamically tracks memory consumption of variables across assignments, loops, and conditionals.
- **Memory Footprint Analysis**: Computes maximum memory usage by analyzing execution paths, accounting for dynamic changes in data structures.

### Data Aggregation
- **Parallel Result Aggregation**: Combines partial results (e.g., sum, count, min, max, frequency maps) from parallel nodes into a cohesive report using the `Aggregator` class and `PartialResult` dataclass in `aggregator.py`.

### Data Generation
- **Large-Scale CSV Generation**: Creates large CSV files with numerical data for testing parallel workflows. The `generator.py` script leverages `numpy` for efficient data generation.

### Task Scheduling
- **Parallel Task Orchestration**: Schedules tasks based on DDG and memory estimation analysis to ensure data dependencies are resolved, maximizing parallel execution efficiency.

---

## 🛠️ Installation  <a name="installation"></a>

To set up the Parallelization Module, ensure you have **Python 3.8+** installed. Follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/parallelization-module.git
   cd parallelization-module
   ```

2. Install dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

   Required packages:
   - `pandas`
   - `tabulate`
   - `termcolor`
   - `networkx`
   - `matplotlib`
   - `astor`

---

## 🚀 Usage

The main entry point for code analysis and parallelization is `Parallelizer.py`.

### Steps
1. **Prepare Input Code**:
   - Place Python code files for analysis (e.g., `sample.py`) in the `testcases/` directory.
   - Example: The project includes `testcases/sobel/sobel.py` for demonstration.

2. **Run Parallelizer**:
   ```bash
   python Parallelizer.py <script path>
   ```
   - This script performs syntax validation, DDG construction, dependency analysis, and memory estimation.

3. **Review Outputs**:
   - **Syntax Errors**: Logged to `errors.txt` if issues are detected.
   - **DDG Refined Output**: saved as JSON files (e.g., `temp/ddg_parsed`).
   - **Memory Footprint**: saved as JSON files (e.g., `temp/memory_parsed`).

### Example: Generating Test Data
To create a large CSV file for testing:
```bash
python generator.py
```
This generates `sales_data2.csv` with 10,000,000 rows and 20 columns of random integer data, ideal for simulating large-scale parallel processing.

---

## 📁 Project Structure

```
parallelization-module/
├── aggregator.py           # Aggregates parallel computation results
├── DDG.py                 # Builds and visualizes Data Dependency Graphs
├── Memory_Estimator.py    # Estimates memory usage for variables and data structures
├── Parallelizer.py        # Main script for code analysis and parallelization
├── generator.py           # Generates large CSV datasets for testing
├── requirements.txt       # Lists required Python dependencies
├── errors.txt             # Logs syntax errors (generated)
├── output.csv             # Example output file (generated)
├── testcases/             # Directory for input Python code files
│   └── sobel/
│       └── sobel.py
└── temp/                  # Stores intermediate DDG JSON files
    ├── graph_0_nodes.json
    └── graph_0_edges.json
```

---

## 🐛 Error Handling

- **Syntax Errors**: Detected during initial validation and logged to `errors.txt` with detailed error messages.
- **Dependency Issues**: The DDG ensures tasks are scheduled only when dependencies are resolved, preventing runtime errors.
- **Memory Overflows**: Memory estimation helps identify potential bottlenecks before execution.

---

## 🤝 Contributing

We welcome contributions to enhance the Parallelization Module! To contribute:

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit changes:
   ```bash
   git commit -m "Add YourFeature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a Pull Request on GitHub.


---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

