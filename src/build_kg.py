"""
Pharmacy Delivery Ontology – Knowledge Graph Builder & SHACL Validator
=======================================================================
This script:
  1. Loads the existing OWL ontology (pharmacy.owl)
  2. Loads the RDF/Turtle knowledge graph (pharmacy-kg.ttl)
  3. Runs all 5 SPARQL queries and prints results
  4. Validates the graph against SHACL shapes and reports violations

Dependencies:
    pip install rdflib pyshacl

Usage:
    python src/build_kg.py
"""

import sys
from pathlib import Path

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef
    from rdflib.namespace import NamespaceManager
except ImportError:
    print("ERROR: rdflib not found. Install with: pip install rdflib")
    sys.exit(1)

try:
    import pyshacl
except ImportError:
    print("WARNING: pyshacl not found. SHACL validation will be skipped.")
    print("         Install with: pip install pyshacl")
    pyshacl = None

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
OWL_FILE   = BASE_DIR / "ontology" / "pharmacy-delivery.owl"   # extended OWL
TTL_FILE   = BASE_DIR / "pharmacy-kg.ttl"
SHACL_FILE = BASE_DIR / "shacl" / "pharmacy_shapes.shacl"
QUERY_DIR  = BASE_DIR / "queries"

# ── Namespace ─────────────────────────────────────────────────────────────────
PDO = Namespace("http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#")

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 – Load graphs
# ─────────────────────────────────────────────────────────────────────────────

def load_graphs() -> Graph:
    """Merge OWL ontology and KG Turtle into a single rdflib Graph."""
    g = Graph()
    g.bind("pdo", PDO)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    # Load Turtle KG (always present)
    if TTL_FILE.exists():
        g.parse(str(TTL_FILE), format="turtle")
        print(f"[OK] Loaded KG  : {TTL_FILE.name}  ({len(g)} triples)")
    else:
        print(f"[WARN] KG file not found: {TTL_FILE}")

    # Load OWL ontology if available
    if OWL_FILE.exists():
        g.parse(str(OWL_FILE), format="xml")
        print(f"[OK] Loaded OWL : {OWL_FILE.name}  ({len(g)} triples total)")
    else:
        # Fall back to the original pharmacy.owl in repo root
        original_owl = BASE_DIR / "pharmacy.owl"
        if original_owl.exists():
            g.parse(str(original_owl), format="xml")
            print(f"[OK] Loaded OWL : pharmacy.owl  ({len(g)} triples total)")
        else:
            print("[WARN] No OWL ontology file found – continuing with KG only.")

    return g


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 2 – Print graph summary
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(g: Graph) -> None:
    print("\n" + "=" * 60)
    print("  KNOWLEDGE GRAPH SUMMARY")
    print("=" * 60)

    classes = [
        ("User",           PDO.User),
        ("Medicine",       PDO.Medicine),
        ("Order",          PDO.Order),
        ("Pharmacy",       PDO.Pharmacy),
        ("Prescription",   PDO.Prescription),
        ("DeliveryPerson", PDO.DeliveryPerson),
    ]
    for label, cls in classes:
        count = sum(1 for _ in g.subjects(RDF.type, cls))
        print(f"  {label:<20} : {count} instances")

    print(f"\n  Total triples        : {len(g)}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 – Run SPARQL queries
# ─────────────────────────────────────────────────────────────────────────────

QUERIES = {
    "query1_users_and_orders.rq":      "Q1 – Users and their Orders",
    "query2_prescription_medicines.rq": "Q2 – Prescription Medicines",
    "query3_orders_by_courier.rq":     "Q3 – Orders by Courier",
    "query4_pharmacy_medicines.rq":    "Q4 – Pharmacy Medicine Stock",
    "query5_full_order_pipeline.rq":   "Q5 – Full Order Pipeline",
}


def run_queries(g: Graph) -> None:
    print("\n" + "=" * 60)
    print("  SPARQL QUERY RESULTS")
    print("=" * 60)

    for filename, title in QUERIES.items():
        query_file = QUERY_DIR / filename
        if not query_file.exists():
            print(f"\n  [SKIP] {title} – file not found: {filename}")
            continue

        sparql = query_file.read_text(encoding="utf-8")
        print(f"\n{'─' * 60}")
        print(f"  {title}")
        print(f"  File: {filename}")
        print("─" * 60)

        try:
            results = g.query(sparql)
            vars_   = [str(v) for v in results.vars]

            if not vars_:
                print("  (no variables in result)")
                continue

            # Header
            col_width = max(16, 80 // len(vars_))
            header = "  " + " | ".join(v[:col_width].ljust(col_width) for v in vars_)
            print(header)
            print("  " + "-" * (len(header) - 2))

            row_count = 0
            for row in results:
                cells = []
                for v in vars_:
                    val = row[v]
                    if val is None:
                        cell = "(none)"
                    else:
                        cell = str(val).replace(
                            "http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#", ""
                        )
                    cells.append(cell[:col_width].ljust(col_width))
                print("  " + " | ".join(cells))
                row_count += 1

            if row_count == 0:
                print("  (no results – check that the KG individuals match the query patterns)")
            else:
                print(f"\n  → {row_count} row(s) returned.")

        except Exception as exc:
            print(f"  [ERROR] Query failed: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4 – SHACL Validation
# ─────────────────────────────────────────────────────────────────────────────

def run_shacl(g: Graph) -> None:
    if pyshacl is None:
        print("\n[SKIP] SHACL validation – pyshacl not installed.")
        return

    if not SHACL_FILE.exists():
        print(f"\n[SKIP] SHACL shapes file not found: {SHACL_FILE}")
        return

    print("\n" + "=" * 60)
    print("  SHACL VALIDATION")
    print("=" * 60)

    shacl_graph = Graph()
    shacl_graph.parse(str(SHACL_FILE), format="turtle")

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=g,
        shacl_graph=shacl_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        meta_shacl=False,
        debug=False,
    )

    if conforms:
        print("\n  ✅ Validation PASSED – all instances conform to SHACL shapes.")
    else:
        print("\n  ❌ Validation found constraint violations:\n")
        print(results_text)

    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 5 – Build extended KG programmatically (demo)
# ─────────────────────────────────────────────────────────────────────────────

def add_demo_individual(g: Graph) -> None:
    """
    Demonstrates how to add a new individual programmatically.
    Adds a new User 'Ali' with an Order for 'Ibuprofen'.
    """
    print("\n" + "=" * 60)
    print("  PROGRAMMATIC KG EXTENSION (demo)")
    print("=" * 60)

    # New user
    ali = PDO.Ali
    g.add((ali, RDF.type, PDO.User))
    g.add((ali, PDO.firstName,  Literal("Ali",            datatype=XSD.string)))
    g.add((ali, PDO.lastName,   Literal("Ozdemir",        datatype=XSD.string)))
    g.add((ali, PDO.email,      Literal("ali@email.com",  datatype=XSD.string)))
    g.add((ali, PDO.phone,      Literal("+90 530 999 8877", datatype=XSD.string)))

    # New order
    order7 = PDO.Order007
    g.add((order7, RDF.type,         PDO.Order))
    g.add((order7, PDO.orderID,      Literal("ORD-2026-007", datatype=XSD.string)))
    g.add((order7, PDO.orderStatus,  Literal("pending",      datatype=XSD.string)))
    g.add((order7, PDO.totalPrice,   Literal(18.75,          datatype=XSD.decimal)))
    g.add((order7, PDO.deliveryFee,  Literal(5.00,           datatype=XSD.decimal)))
    g.add((order7, PDO.containMedicine, PDO.Ibuprofen))
    g.add((order7, PDO.deliveredBy,  PDO.Courier3))

    # Link user → order
    g.add((ali, PDO.placesOrder, order7))

    print("  Added: pdo:Ali (User) → pdo:Order007 → pdo:Ibuprofen")
    print(f"  Total triples after extension: {len(g)}")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 60)
    print("  PHARMACY DELIVERY ONTOLOGY – KG BUILDER")
    print("=" * 60)

    g = load_graphs()
    print_summary(g)
    run_queries(g)
    add_demo_individual(g)
    run_shacl(g)

    # Serialize merged graph
    out_file = BASE_DIR / "pharmacy-kg-merged.ttl"
    g.serialize(destination=str(out_file), format="turtle")
    print(f"\n[OK] Merged graph saved → {out_file.name}")
    print("\nDone.\n")


if __name__ == "__main__":
    main()
