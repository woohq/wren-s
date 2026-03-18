#!/usr/bin/env python3
"""VESTIGE — World Authoring Webapp

Dual interface:
  - Visual browser for Henry (browse entities, see relationships, read prose)
  - Structured API for Wren (context-aware endpoints for lore-aware editing)

Usage: python3 webapp.py [--port 8090]
"""

import http.server
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse, parse_qs

DATA_DIR = Path(__file__).parent / "data"
DESIGN_DIR = Path(__file__).parent / "design"
FRONTEND_PATH = Path(__file__).parent / "webapp.html"
PORT = 8090

# ─── Data Layer ──────────────────────────────────────────────────────────────

class WorldData:
    """Loads, indexes, and queries all Vestige entity data."""

    # Fields that contain entity ID references (not prose text)
    REF_FIELDS = {
        "territory", "archetype_filter", "archetype_tendency",
        "archetype_tendencies", "starting_traits", "trait_tendencies",
        "trait_requires_any", "trait_excludes", "worship_tendency",
        "attunement_tendency", "attunement_affinity", "attunement",
        "faction_present", "era", "culture", "place", "region",
    }

    # Fields that contain prose (skip for structural refs)
    PROSE_FIELDS = {
        "text", "description", "consequence_text", "personality",
        "power_manifestation", "limitations", "internal_divisions",
        "acknowledged_flaw", "goal", "leadership", "resources",
        "worship_generates", "dilemma", "story_tendency",
        "emotional_function", "flavor_text",
    }

    def __init__(self):
        self.entities = {}       # {type_name: {entity_id: data}}
        self.all_ids = set()     # all known entity IDs
        self.all_names = {}      # {lowercase_name: (type, id)}
        self.refs_from = defaultdict(list)   # entity_id -> [(target_type, target_id, field)]
        self.refs_to = defaultdict(list)     # entity_id -> [(source_type, source_id, field)]
        self.spawn_forward = defaultdict(list)  # event_id -> [spawned event info]
        self.spawn_backward = {}                # spawned_event_id -> parent_event_id
        self.tag_index = defaultdict(list)       # tag -> [(type, id)]

        self.load_all()
        self.build_indexes()

    def load_all(self):
        """Load all JSON entities from data/ directory."""
        if not DATA_DIR.exists():
            print(f"Warning: data directory not found at {DATA_DIR}")
            return

        for type_dir in sorted(DATA_DIR.iterdir()):
            if not type_dir.is_dir():
                continue
            entity_type = type_dir.name
            self.entities[entity_type] = {}

            for json_file in sorted(type_dir.rglob("*.json")):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Warning: failed to load {json_file}: {e}")
                    continue

                entity_id = data.get("id", json_file.stem)
                # Store file path relative to data dir for reference
                data["_file"] = str(json_file.relative_to(DATA_DIR))
                data["_type"] = entity_type
                if "id" not in data:
                    data["id"] = entity_id

                self.entities[entity_type][entity_id] = data
                self.all_ids.add(entity_id)

        total = sum(len(v) for v in self.entities.values())
        print(f"Loaded {total} entities across {len(self.entities)} types")

    def build_indexes(self):
        """Build cross-reference and tag indexes."""
        # First pass: collect all IDs and names
        for entity_type, entities in self.entities.items():
            for entity_id, data in entities.items():
                name = data.get("name", "")
                if name:
                    self.all_names[name.lower()] = (entity_type, entity_id)

        # Second pass: find references and build indexes
        for entity_type, entities in self.entities.items():
            for entity_id, data in entities.items():
                # Index tags
                for tag in data.get("tags", []):
                    self.tag_index[tag].append((entity_type, entity_id))

                # Find structural references
                self._index_refs(entity_type, entity_id, data)

                # Index spawn chains (events only)
                self._index_spawns(entity_type, entity_id, data)

        ref_count = sum(len(v) for v in self.refs_from.values())
        spawn_count = sum(len(v) for v in self.spawn_forward.values())
        print(f"Indexed {ref_count} references, {spawn_count} spawn links")

    def _index_refs(self, entity_type, entity_id, data, path=""):
        """Recursively find entity ID references in data."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ("id", "_file", "_type", "created", "tags"):
                    continue
                if key in self.PROSE_FIELDS:
                    continue
                self._index_refs(entity_type, entity_id, value, f"{path}.{key}")
        elif isinstance(data, list):
            for item in data:
                self._index_refs(entity_type, entity_id, item, path)
        elif isinstance(data, str):
            if data in self.all_ids and data != entity_id:
                # Found a reference to another entity
                target_type = self._find_type(data)
                if target_type:
                    field = path.lstrip(".")
                    self.refs_from[entity_id].append((target_type, data, field))
                    self.refs_to[data].append((entity_type, entity_id, field))

    def _index_spawns(self, entity_type, entity_id, data):
        """Index spawn chain links for events."""
        if entity_type != "events":
            return
        for choice_idx, choice in enumerate(data.get("choices", [])):
            spawns = choice.get("spawns", {})
            for spawn_type, spawn_list in spawns.items():
                if not isinstance(spawn_list, list):
                    continue
                for spawn in spawn_list:
                    if isinstance(spawn, dict) and "id" in spawn:
                        self.spawn_forward[entity_id].append({
                            "id": spawn["id"],
                            "type": spawn_type,
                            "choice_idx": choice_idx,
                            "delay": spawn.get("delay", ""),
                            "description": spawn.get("description", ""),
                        })
                        self.spawn_backward[spawn["id"]] = entity_id

    def _find_type(self, entity_id):
        """Find which type an entity ID belongs to."""
        for entity_type, entities in self.entities.items():
            if entity_id in entities:
                return entity_type
        return None

    # ─── Query Methods ───────────────────────────────────────────────────

    def get_types(self):
        """List all entity types with counts."""
        return {t: len(e) for t, e in sorted(self.entities.items())}

    def get_entities(self, entity_type):
        """List all entities of a type (summary only)."""
        entities = self.entities.get(entity_type, {})
        return [
            {
                "id": eid,
                "name": data.get("name", eid),
                "tags": data.get("tags", []),
                "_file": data.get("_file", ""),
            }
            for eid, data in sorted(entities.items(), key=lambda x: x[1].get("name", x[0]))
        ]

    def get_entity(self, entity_type, entity_id):
        """Get a single entity with enriched cross-references."""
        entities = self.entities.get(entity_type, {})
        data = entities.get(entity_id)
        if not data:
            return None

        # Enrich with cross-reference info
        enriched = dict(data)
        enriched["_refs_from"] = [
            {"type": t, "id": i, "field": f}
            for t, i, f in self.refs_from.get(entity_id, [])
        ]
        enriched["_refs_to"] = [
            {"type": t, "id": i, "field": f}
            for t, i, f in self.refs_to.get(entity_id, [])
        ]
        enriched["_spawns"] = self.spawn_forward.get(entity_id, [])
        if entity_id in self.spawn_backward:
            enriched["_born_from"] = self.spawn_backward[entity_id]

        return enriched

    def search(self, query, entity_type=None, tag=None):
        """Full-text search across entities."""
        results = []
        query_lower = query.lower() if query else ""

        for etype, entities in self.entities.items():
            if entity_type and etype != entity_type:
                continue
            for eid, data in entities.items():
                if tag and tag not in data.get("tags", []):
                    continue
                if query_lower:
                    searchable = json.dumps(data, default=str).lower()
                    if query_lower not in searchable:
                        continue
                results.append({
                    "type": etype,
                    "id": eid,
                    "name": data.get("name", eid),
                    "tags": data.get("tags", []),
                })
        return results

    def get_graph(self, center_type=None, center_id=None, depth=2):
        """Get relationship graph as nodes + edges."""
        nodes = {}
        edges = []

        if center_type and center_id:
            # Subgraph centered on a specific entity
            visited = set()
            self._walk_graph(center_type, center_id, depth, nodes, edges, visited)
        else:
            # Full graph (only structurally referenced entities)
            for entity_type, entities in self.entities.items():
                for entity_id, data in entities.items():
                    if self.refs_from.get(entity_id) or self.refs_to.get(entity_id):
                        nodes[entity_id] = {
                            "id": entity_id,
                            "type": entity_type,
                            "name": data.get("name", entity_id),
                        }

            seen_edges = set()
            for source_id, refs in self.refs_from.items():
                for target_type, target_id, field in refs:
                    edge_key = (source_id, target_id)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append({
                            "source": source_id,
                            "target": target_id,
                            "field": field,
                        })

        return {"nodes": list(nodes.values()), "edges": edges}

    def _walk_graph(self, entity_type, entity_id, depth, nodes, edges, visited):
        """Walk graph from a center node to given depth."""
        if entity_id in visited or depth < 0:
            return
        visited.add(entity_id)

        data = self.entities.get(entity_type, {}).get(entity_id)
        if not data:
            return

        nodes[entity_id] = {
            "id": entity_id,
            "type": entity_type,
            "name": data.get("name", entity_id),
        }

        # Walk outgoing refs
        for target_type, target_id, field in self.refs_from.get(entity_id, []):
            edges.append({"source": entity_id, "target": target_id, "field": field})
            self._walk_graph(target_type, target_id, depth - 1, nodes, edges, visited)

        # Walk incoming refs
        for source_type, source_id, field in self.refs_to.get(entity_id, []):
            edges.append({"source": source_id, "target": entity_id, "field": field})
            self._walk_graph(source_type, source_id, depth - 1, nodes, edges, visited)

    def get_stats(self):
        """Overall world statistics."""
        stats = {
            "total_entities": sum(len(e) for e in self.entities.values()),
            "types": self.get_types(),
            "total_references": sum(len(v) for v in self.refs_from.values()),
            "total_spawn_chains": sum(len(v) for v in self.spawn_forward.values()),
            "total_tags": len(self.tag_index),
            "top_tags": sorted(
                [(tag, len(ents)) for tag, ents in self.tag_index.items()],
                key=lambda x: -x[1]
            )[:20],
        }

        # Word counts (prose volume)
        total_words = 0
        type_words = {}
        for entity_type, entities in self.entities.items():
            type_total = 0
            for data in entities.values():
                for field in self.PROSE_FIELDS:
                    text = data.get(field, "")
                    if isinstance(text, str):
                        type_total += len(text.split())
                # Count choice text and consequence text
                for choice in data.get("choices", []):
                    for f in ("text", "consequence_text"):
                        t = choice.get(f, "")
                        if isinstance(t, str):
                            type_total += len(t.split())
            type_words[entity_type] = type_total
            total_words += type_total

        stats["total_words"] = total_words
        stats["words_by_type"] = type_words
        return stats

    def get_coverage(self):
        """Coverage analysis — where are the gaps?"""
        coverage = {}

        # Events by age/category
        event_ages = defaultdict(int)
        event_archetypes = defaultdict(int)
        events_with_spawns = 0
        events_total = len(self.entities.get("events", {}))

        for eid, data in self.entities.get("events", {}).items():
            age = data.get("age", "unknown")
            event_ages[age] += 1

            filters = data.get("archetype_filter", [])
            if filters and filters != ["any"]:
                for a in filters:
                    event_archetypes[a] += 1
            else:
                event_archetypes["universal"] += 1

            for choice in data.get("choices", []):
                if choice.get("spawns"):
                    events_with_spawns += 1
                    break

        coverage["events_by_age"] = dict(event_ages)
        coverage["events_by_archetype"] = dict(event_archetypes)
        coverage["events_with_spawn_chains"] = events_with_spawns
        coverage["events_total"] = events_total

        # Scenes by type
        scene_types = defaultdict(int)
        for sid, data in self.entities.get("scenes", {}).items():
            stype = data.get("scene_type", data.get("_file", "").split("/")[0] if "/" in data.get("_file", "") else "other")
            scene_types[stype] += 1
        coverage["scenes_by_type"] = dict(scene_types)

        # Archetypes with friendship scenes
        archetypes = list(self.entities.get("archetypes", {}).keys())
        archetype_scenes = {a: {"intro": False, "bonding": False, "critical": False} for a in archetypes}
        for sid, data in self.entities.get("scenes", {}).items():
            name = sid.lower()
            for a in archetypes:
                short = a.replace("_s_", "_").replace("_of_", "_")
                a_short = a.split("_")[0]  # first word
                if a_short in name or short in name:
                    if "intro" in name:
                        archetype_scenes[a]["intro"] = True
                    if "bonding" in name:
                        archetype_scenes[a]["bonding"] = True
                    if "critical" in name:
                        archetype_scenes[a]["critical"] = True
        coverage["archetype_scenes"] = archetype_scenes

        # Cards by attunement
        card_attunements = defaultdict(int)
        for cid, data in self.entities.get("cards", {}).items():
            att = data.get("attunement", "universal")
            card_attunements[att] += 1
        coverage["cards_by_attunement"] = dict(card_attunements)

        return coverage

    def validate(self):
        """Run validation checks across all data."""
        issues = []

        for entity_type, entities in self.entities.items():
            for entity_id, data in entities.items():
                # Check for missing name
                if "name" not in data:
                    issues.append({
                        "type": "warning",
                        "entity": f"{entity_type}/{entity_id}",
                        "message": "Missing 'name' field",
                    })

                # Check for empty tags
                if not data.get("tags"):
                    issues.append({
                        "type": "warning",
                        "entity": f"{entity_type}/{entity_id}",
                        "message": "No tags",
                    })

        # Check for broken spawn references
        for event_id, spawns in self.spawn_forward.items():
            for spawn in spawns:
                sid = spawn["id"]
                if sid in self.all_ids:
                    # Spawned event already exists as authored content
                    pass
                # Note: most spawned events are FUTURE content, not yet authored

        # Check for orphaned references
        for entity_id, refs in self.refs_from.items():
            for target_type, target_id, field in refs:
                if target_id not in self.all_ids:
                    issues.append({
                        "type": "error",
                        "entity": f"{self._find_type(entity_id)}/{entity_id}",
                        "message": f"References non-existent entity '{target_id}' in {field}",
                    })

        return {"issues": issues, "total": len(issues)}

    # ─── Context API ─────────────────────────────────────────────────────

    def get_context_writing(self, params):
        """Get context for writing a specific entity.

        Params: archetype, place, culture, era, age, traits (comma-sep)
        Returns everything relevant to that writing context.
        """
        archetype = params.get("archetype", [None])[0]
        place = params.get("place", [None])[0]
        culture = params.get("culture", [None])[0]
        era = params.get("era", [None])[0]
        age = params.get("age", [None])[0]
        traits = params.get("traits", [""])[0].split(",") if params.get("traits") else []
        traits = [t.strip() for t in traits if t.strip()]

        context = {}

        # The archetype
        if archetype and archetype in self.entities.get("archetypes", {}):
            context["archetype"] = self.entities["archetypes"][archetype]

        # The place
        if place and place in self.entities.get("places", {}):
            context["place"] = self.entities["places"][place]

        # The culture
        if culture and culture in self.entities.get("cultures", {}):
            context["culture"] = self.entities["cultures"][culture]
        elif place:
            # Try to find culture from place tags or references
            place_data = self.entities.get("places", {}).get(place, {})
            for ref_type, ref_id, field in self.refs_from.get(place, []):
                if ref_type == "cultures":
                    context["culture"] = self.entities["cultures"].get(ref_id)
                    break

        # The era
        if era and era in self.entities.get("eras", {}):
            context["era"] = self.entities["eras"][era]

        # Requested traits
        context["traits"] = []
        for t in traits:
            if t in self.entities.get("traits", {}):
                context["traits"].append(self.entities["traits"][t])

        # Factions in this territory/place
        context["factions"] = []
        for fid, fdata in self.entities.get("factions", {}).items():
            territory = fdata.get("territory", [])
            if place and place in territory:
                context["factions"].append({"id": fid, "name": fdata.get("name"), "goal": fdata.get("goal")})

        # Gods worshipped by this culture
        context["gods"] = []
        culture_data = context.get("culture")
        if culture_data:
            for god_id in culture_data.get("worship_tendency", []):
                if god_id in self.entities.get("gods", {}):
                    god = self.entities["gods"][god_id]
                    context["gods"].append({"id": god_id, "name": god.get("name"), "domain": god.get("domain")})

        # Existing events matching this context
        context["existing_events"] = []
        for eid, edata in self.entities.get("events", {}).items():
            matches = True
            if age and edata.get("age") and edata["age"] != age:
                matches = False
            if archetype:
                af = edata.get("archetype_filter", ["any"])
                if af != ["any"] and archetype not in af:
                    matches = False
            if matches:
                context["existing_events"].append({
                    "id": eid,
                    "name": edata.get("name"),
                    "age": edata.get("age"),
                    "tags": edata.get("tags", []),
                    "choice_count": len(edata.get("choices", [])),
                    "has_spawns": any(c.get("spawns") for c in edata.get("choices", [])),
                })

        # Characters in this area
        context["characters"] = []
        for cid, cdata in self.entities.get("characters", {}).items():
            # Check if character is related to this place/culture
            char_str = json.dumps(cdata).lower()
            if place and place in char_str:
                context["characters"].append({"id": cid, "name": cdata.get("name")})
            elif culture and culture in char_str:
                context["characters"].append({"id": cid, "name": cdata.get("name")})

        # Existing scenes for this archetype
        context["existing_scenes"] = []
        if archetype:
            a_short = archetype.split("_")[0]
            for sid, sdata in self.entities.get("scenes", {}).items():
                if a_short in sid:
                    context["existing_scenes"].append({
                        "id": sid,
                        "name": sdata.get("name", sid),
                    })

        # Coverage gap hint
        if archetype and age:
            matching = len(context["existing_events"])
            context["coverage_hint"] = f"{matching} events match {archetype}/{age}. " + (
                "Good coverage." if matching >= 5 else
                "Thin coverage — more events needed." if matching >= 2 else
                "Very thin — priority gap."
            )

        return context

    def get_context_spawning(self, event_id):
        """Get full spawn chain context for an event."""
        context = {
            "event": None,
            "chain_forward": [],
            "chain_backward": [],
            "thread_siblings": [],
        }

        # The event itself
        event = self.entities.get("events", {}).get(event_id)
        if not event:
            return context
        context["event"] = {
            "id": event_id,
            "name": event.get("name"),
            "choices": len(event.get("choices", [])),
        }

        # Forward chain — what does this event spawn?
        def walk_forward(eid, depth=0):
            if depth > 5:
                return
            for spawn in self.spawn_forward.get(eid, []):
                entry = dict(spawn)
                entry["depth"] = depth
                context["chain_forward"].append(entry)
                walk_forward(spawn["id"], depth + 1)

        walk_forward(event_id)

        # Backward chain — where did this event come from?
        def walk_backward(eid):
            parent = self.spawn_backward.get(eid)
            if parent:
                parent_data = self.entities.get("events", {}).get(parent, {})
                context["chain_backward"].append({
                    "id": parent,
                    "name": parent_data.get("name", parent),
                })
                walk_backward(parent)

        walk_backward(event_id)

        # Thread siblings — other events spawned by the same parent
        parent = self.spawn_backward.get(event_id)
        if parent:
            for spawn in self.spawn_forward.get(parent, []):
                if spawn["id"] != event_id:
                    context["thread_siblings"].append(spawn)

        return context

    def get_context_checking(self, entity_type, entity_id):
        """Validate a specific entity's references and consistency."""
        entity = self.get_entity(entity_type, entity_id)
        if not entity:
            return {"error": "Entity not found"}

        issues = []

        # Check outgoing references
        for ref in entity.get("_refs_from", []):
            if ref["id"] not in self.all_ids:
                issues.append(f"References non-existent '{ref['id']}' ({ref['type']}) in {ref['field']}")

        # Check if this entity is referenced by anything
        incoming = entity.get("_refs_to", [])
        if not incoming and entity_type not in ("traits", "cards", "relationships"):
            issues.append("Not referenced by any other entity — possibly orphaned")

        return {
            "entity": f"{entity_type}/{entity_id}",
            "outgoing_refs": len(entity.get("_refs_from", [])),
            "incoming_refs": len(entity.get("_refs_to", [])),
            "issues": issues,
            "valid": len(issues) == 0,
        }


# ─── HTTP Server ─────────────────────────────────────────────────────────────

class VestigeHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the Vestige webapp."""

    world = None  # Set by main()

    def log_message(self, format, *args):
        # Quieter logging
        if "/api/" in str(args[0]) if args else False:
            return
        super().log_message(format, *args)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # Route
        if path == "" or path == "/":
            self._serve_frontend()
        elif path == "/api/types":
            self._json(self.world.get_types())
        elif path.startswith("/api/entities/"):
            parts = path.split("/")
            if len(parts) == 4:
                # /api/entities/:type
                entity_type = parts[3]
                self._json(self.world.get_entities(entity_type))
            elif len(parts) == 5:
                # /api/entities/:type/:id
                entity_type, entity_id = parts[3], parts[4]
                result = self.world.get_entity(entity_type, entity_id)
                if result:
                    self._json(result)
                else:
                    self._error(404, "Entity not found")
            else:
                self._error(400, "Bad path")
        elif path == "/api/search":
            q = params.get("q", [""])[0]
            t = params.get("type", [None])[0]
            tag = params.get("tag", [None])[0]
            self._json(self.world.search(q, t, tag))
        elif path == "/api/graph":
            self._json(self.world.get_graph())
        elif path.startswith("/api/graph/"):
            parts = path.split("/")
            if len(parts) == 5:
                entity_type, entity_id = parts[3], parts[4]
                depth = int(params.get("depth", [2])[0])
                self._json(self.world.get_graph(entity_type, entity_id, depth))
            else:
                self._error(400, "Bad path")
        elif path == "/api/stats":
            self._json(self.world.get_stats())
        elif path == "/api/coverage":
            self._json(self.world.get_coverage())
        elif path == "/api/validate":
            self._json(self.world.validate())
        elif path == "/api/context/writing":
            self._json(self.world.get_context_writing(params))
        elif path.startswith("/api/context/spawning/"):
            event_id = path.split("/")[-1]
            self._json(self.world.get_context_spawning(event_id))
        elif path.startswith("/api/context/checking/"):
            parts = path.split("/")
            if len(parts) == 6:
                entity_type, entity_id = parts[4], parts[5]
                self._json(self.world.get_context_checking(entity_type, entity_id))
            else:
                self._error(400, "Bad path")
        else:
            self._error(404, "Not found")

    def _serve_frontend(self):
        try:
            with open(FRONTEND_PATH) as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
        except FileNotFoundError:
            self._error(500, "Frontend file not found")

    def _json(self, data):
        body = json.dumps(data, indent=2, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    port = PORT
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    print(f"Loading Vestige world data from {DATA_DIR}...")
    world = WorldData()

    VestigeHandler.world = world

    server = http.server.HTTPServer(("", port), VestigeHandler)
    print(f"\nVESTIGE webapp running at http://localhost:{port}")
    print(f"API available at http://localhost:{port}/api/types")
    print("Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
