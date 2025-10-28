import os
import ast
import inspect
import subprocess
import glob

def get_docstring(node):
    if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
        return None
    return ast.get_docstring(node)

def generate_markdown_for_file(filepath, base_dir):
    with open(filepath, "r") as f:
        content = f.read()
    
    tree = ast.parse(content)
    md = ""

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            md += f"## `class {node.name}`\n\n"
            docstring = get_docstring(node)
            if docstring:
                md += f"{docstring}\n\n"
            
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    md += f"### `def {method.name}`\n\n"
                    docstring = get_docstring(method)
                    if docstring:
                        md += f"{docstring}\n\n"

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            md += f"## `def {node.name}`\n\n"
            docstring = get_docstring(node)
            if docstring:
                md += f"{docstring}\n\n"

    return md

def run_command_and_capture_output(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running command: {e}\n{e.stderr}"

def generate_diagrams(docs_dir):
    images_dir = os.path.join(docs_dir, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Generate package diagram
    run_command_and_capture_output("pyreverse -o dot astra_framework -p astra_packages")
    run_command_and_capture_output(f"dot -Tpng packages_astra_packages.dot -o {images_dir}/packages_astra_framework.png")

    # Generate class diagram
    run_command_and_capture_output("pyreverse -o dot astra_framework -p astra_classes -A --verbose")
    run_command_and_capture_output(f"dot -Tpng classes_astra_classes.dot -o {images_dir}/classes_astra_framework.png")

    # Clean up .dot files
    for dot_file in glob.glob("*.dot"):
        os.remove(dot_file)

def generate_ruff_report(docs_dir):
    report_path = os.path.join(docs_dir, "ruff_report.md")
    with open(report_path, "w") as f:
        f.write("# Ruff Report\n\n")
        f.write("```\n")
        f.write(run_command_and_capture_output("ruff check astra_framework"))
        f.write("```\n")

def generate_radon_report(docs_dir):
    report_path = os.path.join(docs_dir, "radon_report.md")
    with open(report_path, "w") as f:
        f.write("# Radon Report\n\n")
        f.write("## Cyclomatic Complexity (CC)\n\n")
        f.write("```\n")
        f.write(run_command_and_capture_output("radon cc astra_framework -s -a"))
        f.write("```\n")
        f.write("## Raw Metrics\n\n")
        f.write("```\n")
        f.write(run_command_and_capture_output("radon raw astra_framework -s"))
        f.write("```\n")

def main():
    base_dir = "astra_framework"
    docs_dir = "documents/docs"
    
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                filepath = os.path.join(root, file)
                markdown = generate_markdown_for_file(filepath, base_dir)
                if markdown:
                    md_filename = os.path.splitext(os.path.basename(filepath))[0] + ".md"
                    with open(os.path.join(docs_dir, md_filename), "w") as f:
                        f.write(markdown)
    
    generate_diagrams(docs_dir)
    generate_ruff_report(docs_dir)
    generate_radon_report(docs_dir)

if __name__ == "__main__":
    main()
