import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


XMI = "http://www.omg.org/spec/XMI/20131001"


def xmi_type(element):
    """Return the UML/XMI type of an XML element."""
    return element.attrib.get(f"{{{XMI}}}type")


def xmi_id(element):
    """Return the XMI identifier of an XML element."""
    return element.attrib.get(f"{{{XMI}}}id")


def parse_component(element, parent=None):
    """
    Extract a UML component and its directly owned ports.

    Original XMI identifiers are preserved for traceability.
    """
    component = {
        "id": xmi_id(element),
        "name": element.attrib.get("name"),
        "parent": parent,
        "ports": []
    }

    for child in element:
        if xmi_type(child) == "uml:Port":
            component["ports"].append(
                {
                    "id": xmi_id(child),
                    "name": child.attrib.get("name")
                }
            )

    return component


def parse_uml(input_path: Path):
    """
    Parse a UML/XMI architecture and return a normalized representation.

    The normalization preserves:
    - the UML model;
    - component hierarchy;
    - component ports;
    - UML Usage relations;
    - original XMI identifiers;
    - human-readable names for Usage endpoints.
    """
    tree = ET.parse(input_path)
    root = tree.getroot()

    components = []
    usages = []

    # Maps XMI IDs to human-readable names.
    element_names = {}

    # --------------------------------------------------
    # Register the UML model
    # --------------------------------------------------

    model_id = xmi_id(root)
    model_name = root.attrib.get("name", "unnamed")

    if model_id:
        element_names[model_id] = f"Model:{model_name}"

    # --------------------------------------------------
    # Recursive UML traversal
    # --------------------------------------------------

    def walk(element, parent_component=None):
        current_parent = parent_component

        # --------------------------------------------------
        # Components and ports
        # --------------------------------------------------

        if xmi_type(element) == "uml:Component":
            component = parse_component(
                element,
                parent_component
            )

            components.append(component)
            current_parent = component["id"]

            # Register component name.
            if component["id"]:
                element_names[component["id"]] = component["name"]

            # Register each port using Component.port notation.
            for port in component["ports"]:
                if port["id"]:
                    element_names[port["id"]] = (
                        f"{component['name']}.{port['name']}"
                    )

        # --------------------------------------------------
        # Usage relations
        # --------------------------------------------------

        if xmi_type(element) == "uml:Usage":
            usages.append(
                {
                    "id": xmi_id(element),
                    "client": element.attrib.get("client"),
                    "supplier": element.attrib.get("supplier")
                }
            )

        # --------------------------------------------------
        # Recursive traversal
        # --------------------------------------------------

        for child in element:
            walk(child, current_parent)

    walk(root)

    # --------------------------------------------------
    # Resolve Usage endpoints
    # --------------------------------------------------

    unresolved_endpoints = set()

    for usage in usages:
        client_id = usage["client"]
        supplier_id = usage["supplier"]

        if client_id in element_names:
            usage["client_name"] = element_names[client_id]
        else:
            usage["client_name"] = client_id
            unresolved_endpoints.add(client_id)

        if supplier_id in element_names:
            usage["supplier_name"] = element_names[supplier_id]
        else:
            usage["supplier_name"] = supplier_id
            unresolved_endpoints.add(supplier_id)

    # Remove possible None values from unresolved endpoints.
    unresolved_endpoints.discard(None)

    # --------------------------------------------------
    # Normalized representation
    # --------------------------------------------------

    result = {
        "model": {
            "id": model_id,
            "name": model_name
        },
        "components": components,
        "usages": usages
    }

    return result, unresolved_endpoints


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert a UML/XMI architecture into a normalized "
            "JSON representation for RAISE2."
        )
    )

    parser.add_argument(
        "input",
        help="Input UML/XMI file."
    )

    parser.add_argument(
        "output",
        help="Output normalized JSON file."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Input UML file does not exist: {input_path}"
        )

    result, unresolved_endpoints = parse_uml(input_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------
    # Execution summary
    # --------------------------------------------------

    component_count = len(result["components"])

    port_count = sum(
        len(component["ports"])
        for component in result["components"]
    )

    usage_count = len(result["usages"])

    print(f"Components: {component_count}")
    print(f"Ports: {port_count}")
    print(f"Usages: {usage_count}")

    if unresolved_endpoints:
        print(
            "WARNING: unresolved Usage endpoints: "
            f"{len(unresolved_endpoints)}"
        )

        for endpoint in sorted(unresolved_endpoints):
            print(f"  - {endpoint}")
    else:
        print("Usage endpoints: all resolved")

    print(f"Written to: {output_path}")


if __name__ == "__main__":
    main()
