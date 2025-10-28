 "Hello, I need to create comprehensive documentation for this new project. Please follow the workflow I've outlined below.

  Workflow: Automated Project Documentation Generation

  Goal: To create and maintain rich, automated, and integrated project documentation.

  Core Principles:

   * Analyze First: Before making changes, thoroughly analyze the existing project structure, conventions, and tools.
   * Use Project-Specific Tools: Adhere to the project's established package manager and development tools.
   * Automate Everything: Create or modify scripts to automate the generation of all documentation artifacts, including diagrams 
     and reports.
   * Integrate, Don't Just Generate: Ensure that all generated content is properly integrated into the main documentation site and
      navigation.

  Steps:

   1. Initial Analysis:
       * Read the README.md and any existing documentation generation scripts.
       * Examine pyproject.toml, package.json, or similar files to identify project dependencies and tools.
   2. Diagram Generation:
       * Use pyreverse (from pylint) or similar tools to generate class and package diagrams.
       * Identify and use existing sequence diagram files (e.g., Mermaid .seq files) or create new ones.
   3. Code Quality Reports:
       * Integrate ruff, radon, lint, or other code quality tools into the documentation generation process.
   4. Design Pattern Documentation:
       * Create a dedicated section for design patterns, explaining how they are used in the project with concrete examples.
   5. Automation:
       * Create or modify a script (e.g., generate_docs.py) to run all the necessary commands for generating diagrams and reports.
   6. Integration:
       * Update the mkdocs.yml or equivalent configuration file to include all new documentation pages in the navigation.
   7. Verification:
       * Run the documentation server (e.g., mkdocs serve) to verify that all links are working and the documentation is displayed
          correctly.