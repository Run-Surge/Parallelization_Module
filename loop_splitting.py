import networkx as nx
import matplotlib.pyplot as plt
import csv
import time

def detect_and_split_loops(graph):
    """
    Detects and removes self-loops and cycles in a directed graph.
    
    Args:
        graph (networkx.DiGraph): A directed graph.

    Returns:
        networkx.DiGraph: A modified acyclic graph.
        list: List of removed edges.
        dict: Performance analysis times.
    """
    start_time = time.time()
    
    modified_graph = graph.copy()
    removed_edges = []
    performance = {}

    # Step 1: Remove Self-Loops
    t1 = time.time()
    self_loops = list(nx.selfloop_edges(modified_graph))
    for u, v in self_loops:
        modified_graph.remove_edge(u, v)
        removed_edges.append((u, v))
        print(f"Removed self-loop: ({u}, {v})")
    performance["self_loop_removal"] = time.time() - t1

    # Step 2: Detect and Break Cycles
    t2 = time.time()
    cycles = list(nx.simple_cycles(modified_graph))
    performance["cycle_detection"] = time.time() - t2

    t3 = time.time()
    while cycles:
        for cycle in cycles:
            if len(cycle) > 1:
                # Select an edge to remove (heuristic: lowest-degree node)
                edge_to_remove = None
                min_degree = float('inf')

                for i in range(len(cycle)):
                    u, v = cycle[i], cycle[(i + 1) % len(cycle)]  # Edge (u -> v)
                    degree = modified_graph.degree[u]

                    if degree < min_degree:
                        min_degree = degree
                        edge_to_remove = (u, v)

                # Remove the selected edge
                if edge_to_remove and modified_graph.has_edge(*edge_to_remove):
                    modified_graph.remove_edge(*edge_to_remove)
                    removed_edges.append(edge_to_remove)
                    print(f"Removed edge {edge_to_remove} to break cycle: {cycle}")

        # Recompute cycles after breaking
        cycles = list(nx.simple_cycles(modified_graph))

    performance["cycle_removal"] = time.time() - t3
    performance["total_runtime"] = time.time() - start_time

    return modified_graph, removed_edges, performance


def visualize_graph(graph, title, filename):
    """
    Visualizes a directed graph using Matplotlib and saves it as an image.
    
    Args:
        graph (networkx.DiGraph): The graph to visualize.
        title (str): Title of the graph.
        filename (str): Output image filename.
    """
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=12)
    plt.title(title)
    plt.savefig(filename)
    plt.show()


def export_to_csv(edges, filename):
    """
    Exports the list of edges to a CSV file.
    
    Args:
        edges (list): List of (node1, node2) tuples.
        filename (str): Output CSV filename.
    """
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Node1", "Node2"])
        writer.writerows(edges)
    print(f"Graph edges saved to {filename}")


def run_test_cases():
    test_cases = [
        {
            "name": "Self-loop only",
            "edges": [(1, 1), (1, 2), (2, 3)]
        },
        {
            "name": "Single cycle",
            "edges": [(1, 2), (2, 3), (3, 1), (3, 4)]
        },
        {
            "name": "Multiple cycles",
            "edges": [(1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 6), (6, 3)]
        },
        {
            "name": "Weighted graph with loops",
            "edges": [(1, 2, 10), (2, 3, 5), (3, 1, 8), (3, 4, 2), (4, 5, 3), (5, 6, 6), (6, 3, 7)],
            "weighted": True
        }
    ]

    performance_results = []

    for case in test_cases:
        print("\n" + "="*30)
        print(f"Running Test Case: {case['name']}")
        print("="*30)

        # Create the graph
        G = nx.DiGraph()
        if case.get("weighted", False):
            G.add_weighted_edges_from(case["edges"], weight='weight')
        else:
            G.add_edges_from(case["edges"])

        # Visualize original graph
        visualize_graph(G, f"Original Graph - {case['name']}", f"{case['name'].replace(' ', '_')}_original.png")

        # Detect loops and modify graph
        modified_G, removed_edges, performance = detect_and_split_loops(G)

        # Visualize modified graph
        visualize_graph(modified_G, f"Modified Graph - {case['name']}", f"{case['name'].replace(' ', '_')}_modified.png")

        # Export modified graph edges to CSV
        export_to_csv(list(modified_G.edges()), f"{case['name'].replace(' ', '_')}_edges.csv")

        # Store performance results
        performance_results.append({
            "Test Case": case["name"],
            "Self-Loop Removal Time (s)": round(performance["self_loop_removal"], 6),
            "Cycle Detection Time (s)": round(performance["cycle_detection"], 6),
            "Cycle Removal Time (s)": round(performance["cycle_removal"], 6),
            "Total Runtime (s)": round(performance["total_runtime"], 6),
        })

        print("Final Modified Graph Edges:", list(modified_G.edges()))
        print("="*30 + "\n")

    # Export performance results
    with open("performance_results.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=performance_results[0].keys())
        writer.writeheader()
        writer.writerows(performance_results)
    print("Performance results saved to performance_results.csv")


# Run test cases
if __name__ == "__main__":
    run_test_cases()
