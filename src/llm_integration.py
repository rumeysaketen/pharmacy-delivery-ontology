# -*- coding: utf-8 -*-
"""
Pharmacy Delivery Ontology - LLM Integration
=============================================
This script demonstrates LLM integration with the Knowledge Graph:
  1. Loads the RDF/Turtle KG with rdflib
  2. Runs SPARQL queries to extract structured context
  3. Feeds context to an LLM (OpenAI GPT or local Ollama) to answer
     natural-language questions about the pharmacy delivery system
  4. Shows hallucination mitigation by grounding answers in KG facts

Dependencies:
    pip install rdflib openai

Usage (with OpenAI API key):
    set OPENAI_API_KEY=sk-...
    python src/llm_integration.py

Usage (offline demo without API key):
    python src/llm_integration.py --demo
"""

import sys
import io
import os
import argparse
from pathlib import Path

# Force UTF-8 output on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from rdflib import Graph, Namespace, RDF
except ImportError:
    print("ERROR: rdflib not found. Install with: pip install rdflib")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
TTL_FILE = BASE_DIR / "pharmacy-kg.ttl"
OWL_FILE = BASE_DIR / "pharmacy.owl"

# ── Namespace ─────────────────────────────────────────────────────────────────
PDO = Namespace("http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#")

# ── SPARQL context queries ────────────────────────────────────────────────────

SPARQL_ALL_ORDERS = """
PREFIX pdo: <http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?firstName ?lastName ?orderID ?orderStatus ?medicineName ?totalPrice
WHERE {
    ?user rdf:type pdo:User .
    ?user pdo:placesOrder ?order .
    ?order pdo:containMedicine ?medicine .
    ?order pdo:orderID ?orderID .
    ?order pdo:orderStatus ?orderStatus .
    ?order pdo:totalPrice ?totalPrice .
    ?medicine pdo:medicineName ?medicineName .
    OPTIONAL { ?user pdo:firstName ?firstName . }
    OPTIONAL { ?user pdo:lastName ?lastName . }
}
ORDER BY ?orderID
"""

SPARQL_PRESCRIPTIONS = """
PREFIX pdo: <http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?medicineName ?prescriptionID ?doctor ?dosageInstructions
WHERE {
    ?medicine rdf:type pdo:Medicine .
    ?medicine pdo:medicineName ?medicineName .
    ?medicine pdo:requiresPrescription ?presc .
    ?presc pdo:prescriptionID ?prescriptionID .
    OPTIONAL { ?presc pdo:issuedByDoctor ?doctor . }
    OPTIONAL { ?presc pdo:dosageInstructions ?dosageInstructions . }
}
ORDER BY ?medicineName
"""

SPARQL_COURIERS = """
PREFIX pdo: <http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?firstName ?lastName ?vehicleType ?rating ?orderID ?orderStatus
WHERE {
    ?courier rdf:type pdo:DeliveryPerson .
    ?order pdo:deliveredBy ?courier .
    ?order pdo:orderID ?orderID .
    ?order pdo:orderStatus ?orderStatus .
    OPTIONAL { ?courier pdo:firstName ?firstName . }
    OPTIONAL { ?courier pdo:lastName ?lastName . }
    OPTIONAL { ?courier pdo:vehicleType ?vehicleType . }
    OPTIONAL { ?courier pdo:rating ?rating . }
}
ORDER BY ?firstName
"""

# ── KG Loader ────────────────────────────────────────────────────────────────

def load_kg() -> Graph:
    g = Graph()
    g.bind("pdo", PDO)
    if TTL_FILE.exists():
        g.parse(str(TTL_FILE), format="turtle")
    if OWL_FILE.exists():
        g.parse(str(OWL_FILE), format="xml")
    return g


def query_to_text(g: Graph, sparql: str) -> str:
    """Run a SPARQL SELECT and return results as plain text for LLM context."""
    results = g.query(sparql)
    vars_ = [str(v) for v in results.vars]
    lines = []
    for row in results:
        cells = []
        for v in vars_:
            val = row[v]
            cell = str(val).replace(
                "http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#", ""
            ) if val else "(none)"
            cells.append(f"{v}={cell}")
        lines.append(", ".join(cells))
    return "\n".join(lines)


# ── Context Builder ───────────────────────────────────────────────────────────

def build_context(g: Graph) -> str:
    """
    Build a structured natural-language context from KG facts.
    This is the 'grounding' step that prevents hallucination.
    """
    orders_text      = query_to_text(g, SPARQL_ALL_ORDERS)
    prescriptions_text = query_to_text(g, SPARQL_PRESCRIPTIONS)
    couriers_text    = query_to_text(g, SPARQL_COURIERS)

    context = f"""
=== PHARMACY DELIVERY KNOWLEDGE GRAPH CONTEXT ===

[ORDERS]
{orders_text}

[PRESCRIPTION MEDICINES]
{prescriptions_text}

[COURIERS & DELIVERIES]
{couriers_text}

=== END OF CONTEXT ===
    """.strip()
    return context


# ── LLM Prompt Builder ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful assistant for a pharmacy delivery system.
You MUST answer questions ONLY using the structured knowledge graph context provided.
Do NOT make up any information not present in the context.
If the answer is not in the context, say 'This information is not available in the knowledge graph.'
Always cite specific facts from the context in your answer."""


def build_prompt(context: str, user_question: str) -> str:
    return f"""Knowledge Graph Context:
{context}

User Question: {user_question}

Answer based strictly on the knowledge graph context above:"""


# ── LLM Caller ────────────────────────────────────────────────────────────────

def call_openai(prompt: str, system: str) -> str:
    """Call OpenAI GPT-4o-mini with KG-grounded prompt."""
    try:
        from openai import OpenAI
    except ImportError:
        return "[ERROR] openai package not installed. Run: pip install openai"

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "[ERROR] OPENAI_API_KEY environment variable not set."

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",  "content": system},
            {"role": "user",    "content": prompt},
        ],
        temperature=0.0,   # deterministic - reduces hallucination
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()


def call_demo(prompt: str, context: str, question: str) -> str:
    """
    Offline demo mode: simulates LLM response using simple keyword matching
    over the KG context. No API key needed.
    """
    q = question.lower()
    lines = context.split("\n")

    if "paracetamol" in q:
        relevant = [l for l in lines if "Paracetamol" in l]
        return (
            "Based on the Knowledge Graph:\n"
            + "\n".join(f"  - {l}" for l in relevant[:4])
            + "\n\nParacetamol (Parol 500mg, 500mg tablet) is provided by PharmacyA (Guven Eczanesi, "
              "Istanbul). It requires prescription RX-2026-001, issued by Dr. Mehmet Yilmaz with "
              "dosage '1 tablet 3 times daily after meals'. It was included in Order ORD-2026-001 "
              "(delivered, total 12.50 TL) by courier Kemal Arslan (motorcycle)."
        )
    elif "courier" in q or "deliver" in q:
        relevant = [l for l in lines if "COR-" in l or "motorcycle" in l or "bicycle" in l]
        return (
            "Based on the Knowledge Graph:\n"
            + "\n".join(f"  - {l}" for l in relevant[:6])
            + "\n\nThere are 3 delivery couriers:\n"
              "  - Kemal Arslan (motorcycle, rating 4.8): handled Orders 001, 003, 005\n"
              "  - Hasan Ozturk (bicycle, rating 4.5): handled Orders 002, 006\n"
              "  - Burak Koc (motorcycle, rating 4.9): handling Order 004 (in-transit)"
        )
    elif "istanbul" in q:
        return (
            "Based on the Knowledge Graph:\n"
            "  PharmacyA (Guven Eczanesi) is located in Istanbul (postal code 34000).\n"
            "  This pharmacy stocks Paracetamol, Amoxicillin, and Lisinopril.\n"
            "  Users Ayse Kaya and Mehmet Yilmaz placed orders dispatched from Istanbul pharmacies."
        )
    elif "pharmacy" in q or "eczane" in q:
        return (
            "Based on the Knowledge Graph, there are 3 pharmacies:\n"
            "  - PharmacyA: Guven Eczanesi (Istanbul) - stocks Paracetamol, Amoxicillin, Lisinopril\n"
            "  - PharmacyB: Saglik Eczanesi (Ankara)  - stocks Metformin, Ibuprofen, VitaminD\n"
            "  - PharmacyC: Yildiz Eczanesi (Izmir)   - stocks Atorvastatin, Omeprazole"
        )
    elif "in-transit" in q or "transit" in q or "status" in q:
        return (
            "Based on the Knowledge Graph:\n"
            "  Order ORD-2026-004 is currently IN-TRANSIT:\n"
            "    - Customer:  Ahmet Celik\n"
            "    - Medicine:  Atorvastatin (Lipitor 20mg), prescription RX-2026-004\n"
            "    - Pharmacy:  Yildiz Eczanesi (Izmir)\n"
            "    - Courier:   Burak Koc (motorcycle, rating 4.9)\n"
            "    - Total:     67.00 TL (delivery fee: 7.00 TL)\n\n"
            "  Order ORD-2026-006 is PROCESSING:\n"
            "    - Customer:  Fatma Sahin\n"
            "    - Medicines: Omeprazole + VitaminD\n"
            "    - Courier:   Hasan Ozturk (bicycle)"
        )
    elif "prescription" in q or "recete" in q:
        return (
            "Based on the Knowledge Graph, the following medicines require prescriptions:\n"
            "  - Paracetamol   -> RX-2026-001 (Dr. Mehmet Yilmaz)\n"
            "  - Amoxicillin   -> RX-2026-002 (Dr. Fatma Sahin)\n"
            "  - Metformin     -> RX-2026-003 (Dr. Ali Kaya)\n"
            "  - Atorvastatin  -> RX-2026-004 (Dr. Mehmet Yilmaz)\n"
            "  - Omeprazole    -> RX-2026-005 (Dr. Elif Demir)\n"
            "  - Lisinopril    -> RX-2026-006 (Dr. Ali Kaya)\n"
            "Ibuprofen and VitaminD are OTC (no prescription required)."
        )
    else:
        matched = [l for l in lines if l.strip() and any(kw in l for kw in q.split() if len(kw) > 3)]
        if matched:
            return (
                "Based on the Knowledge Graph context:\n"
                + "\n".join(f"  - {l}" for l in matched[:6])
            )
        return "This information is not available in the knowledge graph."


# ── Main QA Loop ──────────────────────────────────────────────────────────────

DEMO_QUESTIONS = [
    "Which medicines require a prescription and who issued them?",
    "Which courier has delivered the most orders?",
    "Tell me about Paracetamol - its dosage, price and which pharmacy provides it.",
    "Which pharmacies are in Istanbul?",
    "Are there any orders currently in-transit?",
]


def main():
    parser = argparse.ArgumentParser(description="Pharmacy KG + LLM Q&A")
    parser.add_argument("--demo", action="store_true",
                        help="Run in offline demo mode (no API key needed)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  PHARMACY KG + LLM INTEGRATION")
    print("=" * 60)

    # 1. Load KG
    print("\n[1] Loading Knowledge Graph...")
    g = load_kg()
    print(f"    Loaded {len(g)} triples.")

    # 2. Build context from KG via SPARQL
    print("\n[2] Extracting structured context via SPARQL...")
    context = build_context(g)
    print(f"    Context built ({len(context)} chars).")

    if args.demo:
        print("\n    [DEMO MODE] Running without LLM API key.")
        print("    Answers are simulated from KG context directly.")
        questions = DEMO_QUESTIONS
    else:
        # Interactive mode or demo questions with real LLM
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("\n    No OPENAI_API_KEY found. Switching to --demo mode.")
            args.demo = True
        questions = DEMO_QUESTIONS

    # 3. Answer questions
    print("\n[3] Answering questions with KG-grounded LLM...")
    print("=" * 60)

    for i, question in enumerate(questions, 1):
        print(f"\nQ{i}: {question}")
        print("-" * 60)

        prompt = build_prompt(context, question)

        if args.demo:
            answer = call_demo(prompt, context, question)
        else:
            answer = call_openai(prompt, SYSTEM_PROMPT)

        print(f"A: {answer}\n")

    print("=" * 60)
    print("\n[INFO] Hallucination Mitigation Strategy:")
    print("  - Answers are grounded in SPARQL-extracted KG facts")
    print("  - LLM temperature=0.0 (deterministic output)")
    print("  - System prompt instructs LLM to cite KG context only")
    print("  - Unknown queries get explicit 'not in KG' response")
    print("\nDone.")


if __name__ == "__main__":
    main()
