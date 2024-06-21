from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from random import choice
from string import ascii_letters
from typing import DefaultDict, Dict, List, Union
import dataclasses
import json
import os
import sys

from robot.running import TestSuite, ResourceFile
from robot.utils.robotpath import find_file


PACKAGE_PATH = Path(os.path.abspath(__file__)).parent


@dataclass
class Resource:
    abs_path: str
    deps: List['Resource']
    name: str
    rel_path: str


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        
        return super().default(o)


def get_relative_path(abs_path: str):
    cwd = os.path.abspath(os.curdir)
    return os.path.relpath(abs_path, cwd)


def rec_get_resources(resource: ResourceFile, visits: DefaultDict[Union[str, None], int]) -> List[Resource]:
    visits[resource.name] += 1
    resources = []

    if visits[resource.name] > 1:
        return resources
 
    for _import in resource.imports:
        import_path = _import.name.replace("${/}", "/")
        basedir = os.path.dirname(str(resource.source))
        absolute_path = find_file(import_path, basedir, "Resource")
        _resource = ResourceFile.from_file_system(absolute_path)
        filename = os.path.basename(absolute_path)

        resources.append(Resource(
            absolute_path,
            rec_get_resources(_resource, visits),
            filename,
            get_relative_path(absolute_path)
        ))

    return resources


def gen_node(id: str, node_name: str):
    return f'{id}[{node_name}]'


def gen_id():
    return ''.join(
        choice(ascii_letters)
        for _ in range(5)
    )


def rec_gen_graph(root_node: str, dependencies: List[Resource], node_ids: Dict[str, str]) -> List[str]:
    links = []
    for dep in dependencies:
        node = gen_node(node_ids[dep.abs_path], dep.rel_path)
        links.append(root_node + " --> " + node)
        links += rec_gen_graph(node, dep.deps, node_ids)

    return links


def output_json(input_file, resources):
    input_filename = os.path.basename(input_file)
    abs_path = os.path.abspath(input_file)

    return json.dumps(
        Resource(
            abs_path,
            resources,
            input_filename,
            os.path.relpath(abs_path, abs_path)
        ),
        cls=DataclassJSONEncoder,
        indent=4
    )


def output_html(graph):
    with open(PACKAGE_PATH / "template.html", "rt", encoding='utf-8') as file:
        template = file.read()

    mermaid_js = "file:///" + str(PACKAGE_PATH / "mermaid.min.js").replace("\\", "/")

    return (
        template
            .replace("{{mermaid}}", graph)
            .replace("{{mermaid_js}}", mermaid_js)
    )


def output_mermaid(input_file, resources):
    abs_path = os.path.abspath(input_file)
    node_ids = defaultdict(lambda: gen_id())
    
    return "\n".join(
        ["flowchart-elk TD"] + 
        rec_gen_graph(
            gen_node(node_ids[abs_path], get_relative_path(abs_path)),
            resources,
            node_ids
        )
    )


def run():
    _, *args = sys.argv

    if len(args) != 2:
        print("\n".join(
                ["Usage: robot-graph file format"] +
                ["    file      either a .robot file or a .resource file"] + 
                ["    format    HTML, JSON, Mermaid"]
            )
        )
        sys.exit(0)

    input_file = args[0]
    output_format = args[1]

    if input_file.endswith(".robot"):
        resource = TestSuite.from_file_system(input_file).resource
    elif input_file.endswith(".resource"):
        resource = ResourceFile.from_file_system(input_file)
    else:
        print("The input must be either a .robot or a .resource file")
        sys.exit(1)

    if output_format == "HTML":
        resources = rec_get_resources(resource, defaultdict(lambda: 0))
        graph = output_mermaid(input_file, resources)
        output = output_html(graph)
        extension = ".html"
    elif output_format == "JSON":
        resources = rec_get_resources(resource, defaultdict(lambda: 0))
        output = output_json(input_file, resources)
        extension = ".json"
    elif output_format == "Mermaid":
        resources = rec_get_resources(resource, defaultdict(lambda: 0))
        output = output_mermaid(input_file, resources)
        extension = ".mermaid"
    else:
        print("The output format must be either HTML, JSON or Mermaid")
        sys.exit(1)

    output_file = get_relative_path(str(Path(input_file).absolute())).replace('\\', '.') + ".deps" + extension
    with open(output_file, "wt", encoding='utf-8') as file:
        file.write(output)
