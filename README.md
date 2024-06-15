# robotframework-resource-graph

Generate and visualize the dependency graph of Resource imports in Robot Framework.

## How to use it

```bash
robot-graph file format
```

`file` can be either a .robot file or a .resource file.

`format` can be either HTML, JSON or Mermaid

**Hint**: In case your environment does not allow executing robot-graph, call the Python module directly:

```bash
python -m RobotGraph file format
```

## How does it work

`robot-graph` uses the Robot Framework API to extract the Resource imports from .robot and .resource files. These imports build a dependency graph, which can be represented as a recursive data structure. From this representation one can generate a flow chart using [Mermaid](https://mermaid.js.org/), a JavaScript library for generating diagrams, that can be embedded in an HTML file. `robot-graph` does not need a network connection.
