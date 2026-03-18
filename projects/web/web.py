#!/usr/bin/env python3
"""
web — by Wren

Scans the workspace and shows how projects connect to each other.
A map of the web. The workspace looking at its own structure.
"""

from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def scan_connections() -> dict[str, list[str]]:
    """Scan all projects for cross-references and imports."""
    projects_dir = WORKSPACE / "projects"
    connections: dict[str, list[str]] = {}
    project_names: list[str] = []

    # Get all project directories
    for d in sorted(projects_dir.iterdir()):
        if d.is_dir() and not d.name.startswith('.'):
            project_names.append(d.name)

    # Scan each project's Python files for references to others
    for proj in project_names:
        proj_dir = projects_dir / proj
        refs: set[str] = set()

        for pyfile in proj_dir.glob("*.py"):
            try:
                source = pyfile.read_text()
            except OSError:
                continue

            for other in project_names:
                if other == proj:
                    continue

                other_under = other.replace("-", "_")

                # Only count real structural references:
                # 1. Path-based imports (spec_from_file_location with project name)
                # 2. Direct path references like / "sky" / or / "erasure" /
                # 3. import statements
                real_patterns = [
                    f'/ "{other}"',           # Path segment
                    f"/ '{other}'",           # Path segment
                    f'/ "{other}" /',         # Path segment
                    f'"{other_under}.py"',    # Filename reference
                    f"'{other_under}.py'",    # Filename reference
                    f'"{other}" /',           # Path component
                    f'parent / "{other}"',    # Relative path
                    f"import {other_under}",  # Direct import
                ]

                for pat in real_patterns:
                    if pat in source:
                        refs.add(other)
                        break

        connections[proj] = sorted(refs)

    return connections


def get_project_stats() -> dict[str, int]:
    """Get line counts per project."""
    projects_dir = WORKSPACE / "projects"
    stats = {}
    for d in sorted(projects_dir.iterdir()):
        if d.is_dir() and not d.name.startswith('.'):
            lines = 0
            for pyfile in d.glob("*.py"):
                try:
                    lines += pyfile.read_text().count('\n')
                except OSError:
                    pass
            stats[d.name] = lines
    return stats


def render_map(connections: dict[str, list[str]], stats: dict[str, int]):
    """Render the connection map."""
    # Categorize projects by connectivity
    has_outgoing = {p for p, refs in connections.items() if refs}
    has_incoming = set()
    for refs in connections.values():
        has_incoming.update(refs)

    islands = set(connections.keys()) - has_outgoing - has_incoming  # standalone

    print()
    print("  \033[1m~ web ~\033[0m  the workspace connection map")
    print()

    # Draw connections
    print("  \033[2m── connections ──\033[0m")
    print()

    for proj, refs in sorted(connections.items()):
        if not refs:
            continue

        lines = stats.get(proj, 0)
        size_bar = "█" * max(1, lines // 100)

        print(f"  \033[1;36m{proj}\033[0m \033[2m({lines}L)\033[0m")
        for ref in refs:
            ref_lines = stats.get(ref, 0)
            print(f"    \033[33m└──→\033[0m \033[36m{ref}\033[0m \033[2m({ref_lines}L)\033[0m")
        print()

    # Islands
    if islands:
        print("  \033[2m── standalone ──\033[0m")
        print()
        for proj in sorted(islands):
            lines = stats.get(proj, 0)
            print(f"    \033[2m{proj} ({lines}L)\033[0m")
        print()

    # Summary
    total_lines = sum(stats.values())
    n_connected = len(has_outgoing | has_incoming)
    n_total = len(connections)
    n_edges = sum(len(refs) for refs in connections.values())

    print("  \033[2m── summary ──\033[0m")
    print()
    print(f"    \033[97m{n_total}\033[0m projects, \033[97m{total_lines}\033[0m lines")
    print(f"    \033[97m{n_edges}\033[0m connections between \033[97m{n_connected}\033[0m projects")
    print(f"    \033[97m{len(islands)}\033[0m standalone")
    print()


def main():
    connections = scan_connections()
    stats = get_project_stats()
    render_map(connections, stats)


if __name__ == "__main__":
    main()
