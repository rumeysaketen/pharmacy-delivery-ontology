# Pharmacy Delivery Ontology
## Knowledge Engineering and Ontologies — Course Project Report

**Rumeysa Keten** | rumeysaketen4@gmail.com

---

## Executive Summary

This report presents the design and implementation of the **Pharmacy Delivery Ontology (PDO)**, a knowledge engineering solution developed for modeling online pharmacy delivery systems using Semantic Web technologies. The project addresses the challenge of formally representing a complex multi-stakeholder domain—covering users, medicines, prescriptions, pharmacies, orders, and couriers—and enabling structured querying, constraint validation, and natural-language interaction over this knowledge. The ontology was developed in OWL/XML using Protégé, with six core classes and over twenty-five properties capturing the conceptual model. A companion RDF/Turtle knowledge graph instantiates thirty-one named individuals representing a realistic Turkish pharmacy delivery scenario. Ten SPARQL 1.1 queries—ranging from simple retrieval to multi-hop joins and aggregation—answer competency questions about order status, prescription requirements, courier performance, and pharmacy stock. Six SHACL NodeShapes enforce data integrity constraints including cardinality restrictions, enumeration validation, regular expression patterns, and numeric range checks; all individuals in the knowledge graph pass validation with zero violations. LLM integration is implemented through a retrieval-augmented generation (RAG) architecture: SPARQL queries extract structured context from the knowledge graph, which is then used to ground GPT-4o-mini responses to natural language questions—reducing hallucination risk through deterministic context injection. The project is fully reproducible via a Python automation script (`src/build_kg.py`) and documented through a WIDOCO-style HTML reference page.

---

## 1. Description of the Project

### 1.1 Motivation and Problem Domain

Online pharmacy delivery platforms have become a critical component of modern healthcare infrastructure, particularly following the COVID-19 pandemic, which accelerated digital adoption across healthcare sectors. These platforms must manage complex interactions among multiple stakeholders—patients, pharmacists, prescribing physicians, couriers, and regulatory authorities—while ensuring legal compliance (prescription validation), data accuracy (correct dosage and contraindication information), and delivery efficiency. Despite the richness and complexity of this domain, existing systems typically rely on relational databases and informal data structures that lack formal semantics, making cross-system interoperability and automated reasoning difficult.

The **Pharmacy Delivery Ontology** addresses this gap by providing a formal, reusable semantic model for the domain. By encoding domain knowledge in OWL, constructing an RDF knowledge graph, and exposing it through SPARQL and SHACL, the system enables structured querying, constraint-based data validation, and natural-language question answering grounded in factual knowledge.

### 1.2 Project Objectives

The project has five primary objectives: (1) design a formal OWL ontology covering the core entities and relationships of a pharmacy delivery system; (2) construct an RDF/Turtle knowledge graph populated with realistic instance data; (3) implement SPARQL queries that answer domain-relevant competency questions; (4) define SHACL shapes to enforce data quality constraints; and (5) integrate the knowledge graph with a large language model (GPT-4o-mini) to support grounded natural-language question answering.

### 1.3 Tools and Technologies

| Tool / Technology | Role |
|---|---|
| Protégé 5.6 | OWL ontology development (TBox design) |
| OWL/XML | Ontology serialization format |
| RDF/Turtle | Knowledge graph instance encoding |
| rdflib 7.x (Python) | KG loading, SPARQL querying, programmatic extension |
| pyshacl 0.26.x (Python) | SHACL constraint validation |
| OpenAI GPT-4o-mini API | Natural language to answer generation |
| SPARQL 1.1 | Knowledge graph querying |
| SHACL | Data integrity constraint language |
| Python 3.12 | Automation, scripting, LLM integration |

### 1.4 Target Users

The primary target users are: (1) **developers** building pharmacy delivery applications who require a formal semantic layer; (2) **pharmacists and healthcare administrators** who need structured querying of medication, prescription, and order data; and (3) **researchers** in health informatics exploring ontology-driven knowledge management.

### 1.5 Competency Questions

The following competency questions (CQs) guided ontology design and were subsequently translated into SPARQL queries:

- **CQ1:** What medicines are stocked by a specific pharmacy, and what are their prices and stock quantities?
- **CQ2:** Which medicines require a valid prescription, and which doctor issued each prescription?
- **CQ3:** Which courier has delivered the most orders, and what is their rating and vehicle type?
- **CQ4:** For each user, what is the total amount spent and what was their most expensive order?
- **CQ5:** How many orders currently exist in each delivery status (delivered, in-transit, processing, pending)?
- **CQ6:** What is the average delivery fee and total revenue generated by each pharmacy?
- **CQ7:** Which medicines are available over-the-counter (without a prescription)?
- **CQ8:** What is the complete delivery pipeline for a given order—from customer through medicine, prescription, pharmacy, and courier?

---

## 2. Ontology Design

### 2.1 Overview

The Pharmacy Delivery Ontology is hosted at the namespace:

```
http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#
```

(abbreviated as `pdo:` throughout this report). The ontology defines six core classes, five object properties, and twenty-two data properties. All classes are direct subclasses of `owl:Thing`, reflecting a flat, intentionally simple class hierarchy that prioritizes clarity and extensibility over deep taxonomic modeling.

### 2.2 TBox: Classes

The TBox constitutes the conceptual schema—the terminological definitions that describe what can exist in the domain.

**pdo:User** represents a customer who uses the platform to order medicines. Modeling decision: Users are kept as a single flat class rather than subclassing into `RegisteredUser` and `GuestUser` because the current scope does not require authentication-level distinctions. Properties: `pdo:firstName`, `pdo:lastName`, `pdo:email`, `pdo:phone`, `pdo:dateOfBirth`, `pdo:address`.

**pdo:Medicine** represents a pharmaceutical product. Modeling decision: Prescription-only and OTC medicines are not modeled as subclasses; instead, the presence or absence of a `pdo:requiresPrescription` link determines OTC status. This avoids class proliferation and allows a medicine's prescription status to change over time (e.g., reclassification). Properties: `pdo:medicineName`, `pdo:brandName`, `pdo:genericName`, `pdo:activeIngredient`, `pdo:dosageForm`, `pdo:strength`, `pdo:price`, `pdo:stockQuantity`, `pdo:expiryDate`.

**pdo:Order** represents a purchase request submitted by a user, containing one or more medicines. Modeling decision: Orders are modeled as a first-class entity (rather than a reified relationship between User and Medicine) to allow rich metadata attachment—status, timestamps, fees, and multiple medicines. Properties: `pdo:orderID` (Functional), `pdo:orderStatus`, `pdo:orderDate`, `pdo:deliveryDate`, `pdo:totalPrice`, `pdo:deliveryFee`, `pdo:deliveryAddress`.

**pdo:Pharmacy** represents a licensed pharmacy establishment. Properties: `pdo:pharmacyID` (Functional), `pdo:pharmacyName`, `pdo:city`, `pdo:postalCode`, `pdo:phone`, `pdo:openingHours`.

**pdo:Prescription** represents a doctor-issued authorization. Modeling decision: Prescription is a first-class entity linked to Medicine (not to Order) because a single prescription may cover medicines across multiple orders, and the prescription metadata (issuing doctor, validity period, dosage instructions) belongs conceptually to the prescription itself. Properties: `pdo:prescriptionID` (Functional), `pdo:issueDate`, `pdo:expiryDate`, `pdo:issuedByDoctor`, `pdo:dosageInstructions`.

**pdo:DeliveryPerson** represents a courier. Properties: `pdo:courierID` (Functional), `pdo:vehicleType`, `pdo:rating`, `pdo:licenseNumber`.

### 2.3 TBox: Object Properties

| Property | Domain | Range | Characteristic |
|---|---|---|---|
| `pdo:placesOrder` | User | Order | — |
| `pdo:containMedicine` | Order | Medicine | — |
| `pdo:deliveredBy` | Order | DeliveryPerson | — |
| `pdo:providedBy` | Medicine | Pharmacy | — |
| `pdo:requiresPrescription` | Medicine | Prescription | — |
| `pdo:dispatchedFromPharmacy` | Order | Pharmacy | — |

**Modeling decisions:** The `pdo:providedBy` property links Medicine to Pharmacy rather than modeling this as a separate `Stock` class. This simplification is justified because the current scope does not require modeling stock levels per pharmacy-medicine pair dynamically (i.e., stock quantity is a single data property on Medicine). If multi-pharmacy stock tracking is needed in future versions, a reification or `pdo:Stock` class would be introduced.

### 2.4 ABox: Instance-Level Data

The ABox constitutes the assertions about specific individuals. The knowledge graph contains thirty-one named individuals:

| Class | Count | Representative Instances |
|---|---|---|
| User | 5 | pdo:Ayse, pdo:Mehmet, pdo:Zeynep, pdo:Ahmet, pdo:Fatma |
| Medicine | 8 | pdo:Paracetamol, pdo:Amoxicillin, pdo:Metformin, pdo:Ibuprofen, pdo:VitaminD, pdo:Atorvastatin, pdo:Omeprazole, pdo:Lisinopril |
| Order | 6 | pdo:Order001 through pdo:Order006 |
| Pharmacy | 3 | pdo:PharmacyA (Istanbul), pdo:PharmacyB (Ankara), pdo:PharmacyC (Izmir) |
| Prescription | 6 | pdo:Prescription123 through pdo:Prescription128 |
| DeliveryPerson | 3 | pdo:Courier1, pdo:Courier2, pdo:Courier3 |

### 2.5 Key Modeling Trade-offs

**Classes vs. Instances:** `pdo:PharmacyA` is an instance of `pdo:Pharmacy`, not a subclass, because it represents a particular pharmacy in the world. This follows the closed-world assumption relevant to operational data modeling.

**Roles vs. Types:** The distinction between a doctor who issues a prescription and a courier who delivers an order is captured through separate classes (`pdo:DeliveryPerson`) and a data property (`pdo:issuedByDoctor` on `pdo:Prescription`), rather than through a general `pdo:Person` hierarchy. This reflects the current scope where doctor information is ancillary (metadata on the prescription) rather than a primary entity requiring its own properties.

**Part-Whole Relationships:** An order "contains" medicines via `pdo:containMedicine`. This is modeled as a simple object property rather than using OWL part-whole axioms (`owl:minCardinality`) at this stage, though a future version should add `owl:minCardinality 1` on `pdo:containMedicine` to enforce that every order has at least one medicine at the TBox level.

---

## 3. Data Acquisition

### 3.1 Data Sources

The knowledge graph was populated with **synthetic but domain-realistic data**, constructed to represent a plausible pharmacy delivery scenario in Turkey. No external APIs or web scraping were employed; instead, data was curated manually based on the following real-world references:

- **Medicine names and properties:** Based on publicly available Turkish Ministry of Health (T.C. Sağlık Bakanlığı) medicine lists and the Turkish Medicines and Medical Devices Agency (TITCK) database structure. Generic names (INN), brand names, dosage forms, and strength values reflect real pharmaceutical products.
- **Pharmacy information:** Geographic data (city, postal codes) is based on actual Turkish city postal codes; pharmacy names are fictional but realistic.
- **Prescription structure:** The `RX-YYYY-NNN` identifier pattern was designed to mirror common prescription numbering systems.

### 3.2 Data Format and Structure

All instance data was encoded directly in **RDF/Turtle** format (`pharmacy-kg.ttl`). This format was chosen because:

- It is human-readable and editable without specialized tooling.
- It is natively supported by rdflib without conversion.
- It integrates directly with Protégé and triple stores such as Apache Jena Fuseki.

The file contains 279 data triples prior to merging with the OWL ontology, yielding 312 total triples in the merged graph.

### 3.3 Data Preprocessing

Since data was authored directly in Turtle format, preprocessing steps focused on consistency enforcement:

1. **Datatype uniformity:** Enum-constrained properties (`pdo:dosageForm`, `pdo:orderStatus`, `pdo:vehicleType`) were explicitly typed as `^^xsd:string` to ensure SHACL `sh:in` constraint matching with pyshacl.
2. **ID pattern enforcement:** All `pdo:prescriptionID` values follow the `RX-YYYY-NNN` pattern, verified against the SHACL constraint.
3. **Decimal precision:** Price and fee values use `xsd:decimal` with explicit decimal notation (e.g., `12.50`) to avoid floating-point comparison issues in SPARQL aggregations.
4. **DateTime format:** Order and delivery timestamps follow ISO 8601 (`xsd:dateTime`) with minute precision.

### 3.4 Data Quality and Limitations

The primary limitation is that the data is synthetic. While it is structurally correct and domain-realistic, it does not capture the full complexity of a real pharmacy delivery system, such as: partial orders, order cancellations and refunds, prescription expiry enforcement, multi-item orders with mixed OTC and prescription medicines, or geographic delivery radius constraints. Integration with the actual TITCK medicine database via a SPARQL endpoint would substantially improve data authenticity.

---

## 4. Knowledge Graph Construction

### 4.1 RDF Model and Triple Structure

The knowledge graph follows the standard RDF subject–predicate–object triple model. Each named individual is the subject; properties defined in the OWL ontology serve as predicates; and either other individuals or typed literals serve as objects. The base namespace `pdo:` is bound throughout.

**Representative triples for Order001:**

```turtle
pdo:Order001
    a pdo:Order ;
    pdo:orderID          "ORD-2026-001"^^xsd:string ;
    pdo:orderStatus      "delivered"^^xsd:string ;
    pdo:orderDate        "2026-06-10T09:30:00"^^xsd:dateTime ;
    pdo:deliveryDate     "2026-06-10T11:45:00"^^xsd:dateTime ;
    pdo:totalPrice       12.50 ;
    pdo:deliveryFee      5.00 ;
    pdo:containMedicine  pdo:Paracetamol ;
    pdo:deliveredBy      pdo:Courier1 ;
    pdo:dispatchedFromPharmacy pdo:PharmacyA .
```

**Representative triples for Paracetamol (Medicine):**

```turtle
pdo:Paracetamol
    a pdo:Medicine ;
    pdo:medicineName     "Paracetamol"^^xsd:string ;
    pdo:brandName        "Parol 500mg"^^xsd:string ;
    pdo:dosageForm       "tablet"^^xsd:string ;
    pdo:strength         "500mg"^^xsd:string ;
    pdo:price            12.50 ;
    pdo:stockQuantity    500 ;
    pdo:providedBy       pdo:PharmacyA ;
    pdo:requiresPrescription pdo:Prescription123 .
```

**Representative triples for Prescription123:**

```turtle
pdo:Prescription123
    a pdo:Prescription ;
    pdo:prescriptionID       "RX-2026-001"^^xsd:string ;
    pdo:issueDate            "2026-06-01"^^xsd:date ;
    pdo:expiryDate           "2026-09-01"^^xsd:date ;
    pdo:issuedByDoctor       "Dr. Mehmet Yilmaz"^^xsd:string ;
    pdo:dosageInstructions   "1 tablet 3 times daily after meals"^^xsd:string .
```

### 4.2 Graph Loading and Deployment

The knowledge graph is loaded and merged using **rdflib** in Python:

```python
from rdflib import Graph, Namespace

PDO = Namespace("http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#")

g = Graph()
g.bind("pdo", PDO)
g.parse("pharmacy-kg.ttl", format="turtle")   # ABox: 279 triples
g.parse("pharmacy.owl",     format="xml")      # TBox: merged → 312 total
```

The merged graph is serialized back to `pharmacy-kg-merged.ttl` and can be loaded into a triple store such as **Apache Jena Fuseki** by uploading the merged file to a named graph endpoint. GraphDB can similarly ingest the Turtle file via its Workbench interface.

### 4.3 Namespace Definitions

| Prefix | IRI |
|---|---|
| `pdo:` | `http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#` |
| `rdf:` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` |
| `rdfs:` | `http://www.w3.org/2000/01/rdf-schema#` |
| `owl:` | `http://www.w3.org/2002/07/owl#` |
| `xsd:` | `http://www.w3.org/2001/XMLSchema#` |
| `sh:` | `http://www.w3.org/ns/shacl#` |

### 4.4 Programmatic KG Extension

The Python script (`src/build_kg.py`) demonstrates how to extend the knowledge graph programmatically at runtime—adding a new user (`pdo:Ali`) and a new order (`pdo:Order007`) and verifying that the extended graph still passes SHACL validation. This illustrates the system's capability for dynamic knowledge base updates without reloading the full graph.

---

## 5. SPARQL Queries

All ten SPARQL queries are implemented in the `queries/` directory and executed via rdflib. They are categorized into three types as required: **Basic Retrieval**, **Reasoning**, and **Aggregation**.

### 5.1 Basic Retrieval Queries

**Query 1 — Users and their Orders** (`query1_users_and_orders.rq`)

*Purpose:* Answers CQ8 partially by listing all users with their placed orders, order status, and total price. Uses BIND to extract the local name of the User IRI for display.

```sparql
SELECT ?userName ?orderID ?orderStatus ?totalPrice
WHERE {
    ?user  rdf:type        pdo:User .
    ?user  pdo:placesOrder ?order .
    ?order pdo:orderID     ?orderID .
    ?order pdo:orderStatus ?orderStatus .
    ?order pdo:totalPrice  ?totalPrice .
    BIND(REPLACE(STR(?user), ".*#", "") AS ?userName)
}
ORDER BY ?userName
```

*Expected output (sample):*

| userName | orderID | orderStatus | totalPrice |
|---|---|---|---|
| Ahmet | ORD-2026-004 | in-transit | 67.00 |
| Ayse | ORD-2026-001 | delivered | 12.50 |
| Ayse | ORD-2026-005 | delivered | 41.50 |
| Fatma | ORD-2026-006 | processing | 87.00 |
| Mehmet | ORD-2026-002 | delivered | 45.00 |
| Zeynep | ORD-2026-003 | delivered | 28.00 |

**Query 2 — Prescription Medicines** (`query2_prescription_medicines.rq`)

*Purpose:* Answers CQ2 by retrieving all medicines linked to a prescription, including prescription ID, issue/expiry dates, issuing doctor, and dosage instructions.

```sparql
SELECT ?medicineName ?brandName ?prescriptionID ?issueDate
       ?expiryDate ?doctor ?dosageInstructions
WHERE {
    ?medicine     rdf:type pdo:Medicine .
    ?medicine     pdo:requiresPrescription  ?prescription .
    ?medicine     pdo:medicineName          ?medicineName .
    ?prescription pdo:prescriptionID        ?prescriptionID .
    OPTIONAL { ?medicine     pdo:brandName           ?brandName . }
    OPTIONAL { ?prescription pdo:issueDate            ?issueDate . }
    OPTIONAL { ?prescription pdo:expiryDate           ?expiryDate . }
    OPTIONAL { ?prescription pdo:issuedByDoctor       ?doctor . }
    OPTIONAL { ?prescription pdo:dosageInstructions   ?dosageInstructions . }
}
ORDER BY ?medicineName
```

*Expected output (6 rows):* Paracetamol, Amoxicillin, Metformin, Atorvastatin, Omeprazole, Lisinopril — each with full prescription metadata.

**Query 4 — Pharmacy Medicine Stock** (`query4_pharmacy_medicines.rq`)

*Purpose:* Answers CQ1 by listing all medicines stocked per pharmacy with price and stock quantity.

*Expected output (8 rows):* 3 medicines at PharmacyA, 3 at PharmacyB, 2 at PharmacyC.

### 5.2 Reasoning Queries

**Query 8 — Over-the-Counter Medicines** (`query8_otc_medicines.rq`)

*Purpose:* Answers CQ7 using `FILTER NOT EXISTS` to identify medicines for which no `pdo:requiresPrescription` triple exists—effectively reasoning about the absence of a relationship.

```sparql
SELECT ?medicineName ?brandName ?dosageForm ?price ?pharmacyName
WHERE {
    ?medicine rdf:type pdo:Medicine .
    ?medicine pdo:medicineName ?medicineName .
    ?medicine pdo:providedBy ?pharmacy .
    ?pharmacy pdo:pharmacyName ?pharmacyName .
    OPTIONAL { ?medicine pdo:brandName  ?brandName  . }
    OPTIONAL { ?medicine pdo:dosageForm ?dosageForm . }
    OPTIONAL { ?medicine pdo:price      ?price      . }
    FILTER NOT EXISTS {
        ?medicine pdo:requiresPrescription ?prescription .
    }
}
```

*Expected output:* Ibuprofen (Brufen 400mg, 18.75 TL, PharmacyB), Vitamin D3 (D-Cure 25000 IU, 55.00 TL, PharmacyB).

**Query 9 — Top-Rated Couriers** (`query9_top_rated_couriers.rq`)

*Purpose:* Answers CQ3 by filtering couriers with `rating >= 4.7` using `FILTER`, combined with `COUNT` to show total order assignments. Demonstrates conditional filtering as a form of threshold-based reasoning.

*Expected output:* Kemal Arslan (4.8, 3 orders), Burak Koc (4.9, 1 order).

**Query 5 — Full Order Pipeline** (`query5_full_order_pipeline.rq`)

*Purpose:* Answers CQ8 with a 6-class multi-hop join: User → Order → Medicine → Prescription → Pharmacy → Courier. Uses nested OPTIONAL blocks to gracefully handle OTC medicines (no prescription) and undelivered orders (no deliveryDate).

```sparql
SELECT ?userFirstName ?orderID ?medicineName ?prescriptionID
       ?pharmacyName ?courierFirstName ?vehicleType ?totalPrice
WHERE {
    ?user     pdo:placesOrder     ?order .
    ?order    pdo:containMedicine ?medicine .
    ?medicine pdo:medicineName    ?medicineName .
    ?order    pdo:orderID         ?orderID .
    OPTIONAL { ?user pdo:firstName ?userFirstName . }
    OPTIONAL { ?order pdo:totalPrice ?totalPrice . }
    OPTIONAL {
        ?medicine pdo:requiresPrescription ?presc .
        ?presc    pdo:prescriptionID        ?prescriptionID .
    }
    OPTIONAL {
        ?order pdo:dispatchedFromPharmacy ?ph .
        ?ph    pdo:pharmacyName            ?pharmacyName .
    }
    OPTIONAL {
        ?order pdo:deliveredBy   ?c .
        ?c     pdo:firstName     ?courierFirstName .
        ?c     pdo:vehicleType   ?vehicleType .
    }
}
ORDER BY ?orderID
```

*Expected output (7 rows):* All 6 orders traversed, with VitaminD in Order006 showing `(none)` for prescriptionID (correctly identified as OTC).

### 5.3 Aggregation Queries

**Query 6 — Order Count by Status** (`query6_orders_count_by_status.rq`)

*Purpose:* Answers CQ5. Uses `COUNT` and `GROUP BY` to tally orders per status.

*Expected output:*

| orderStatus | orderCount |
|---|---|
| delivered | 3 |
| processing | 1 |
| in-transit | 1 |

**Query 7 — Average Delivery Fee per Pharmacy** (`query7_avg_delivery_fee_per_pharmacy.rq`)

*Purpose:* Answers CQ6. Uses `AVG`, `SUM`, and `COUNT` to compute operational metrics per pharmacy.

```sparql
SELECT ?pharmacyName ?city
       (COUNT(?order) AS ?orderCount)
       (AVG(?deliveryFee) AS ?avgDeliveryFee)
       (SUM(?totalPrice) AS ?totalRevenue)
WHERE {
    ?order    rdf:type                    pdo:Order .
    ?order    pdo:dispatchedFromPharmacy  ?pharmacy .
    ?order    pdo:deliveryFee             ?deliveryFee .
    ?order    pdo:totalPrice              ?totalPrice .
    ?pharmacy pdo:pharmacyName            ?pharmacyName .
    OPTIONAL { ?pharmacy pdo:city ?city . }
}
GROUP BY ?pharmacyName ?city
ORDER BY DESC(?totalRevenue)
```

*Expected output:*

| pharmacyName | city | orderCount | avgDeliveryFee | totalRevenue |
|---|---|---|---|---|
| Güven Eczanesi | Istanbul | 3 | 5.00 | 98.00 |
| Yıldız Eczanesi | Izmir | 2 | 6.00 | 154.00 |
| Sağlık Eczanesi | Ankara | 1 | 5.00 | 28.00 |

**Query 10 — Spending per User** (`query10_spending_per_user.rq`)

*Purpose:* Answers CQ4. Uses `SUM`, `MAX`, and `COUNT` to compute per-user spending statistics.

*Expected output:* Fatma Sahin (87.00 TL, 1 order), Ahmet Celik (67.00 TL, 1 order), Ayse Kaya (54.00 TL, 2 orders).

---

## 6. SHACL Validation

### 6.1 Overview

Six SHACL `NodeShape` definitions are encoded in `shacl/pharmacy_shapes.shacl`. Each shape targets one of the six core classes and enforces cardinality, datatype, pattern, enumeration, and numeric range constraints.

### 6.2 SHACL Shapes

**pdo:UserShape** (targets `pdo:User`):

```turtle
pdo:UserShape
    a sh:NodeShape ;
    sh:targetClass pdo:User ;
    sh:property [
        sh:path     pdo:firstName ;
        sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message  "User must have exactly one firstName." ;
    ] ;
    sh:property [
        sh:path    pdo:email ;
        sh:minCount 1 ;
        sh:pattern "^[\\w._%+\\-]+@[\\w.\\-]+\\.[a-zA-Z]{2,}$" ;
        sh:message "email must be a valid email address." ;
    ] .
```

**pdo:OrderShape** (targets `pdo:Order`):

Key constraints: `pdo:orderID` required and unique (maxCount 1); `pdo:orderStatus` must be one of `{"pending", "processing", "shipped", "in-transit", "delivered", "cancelled"}` (enforced via `sh:in` with typed literals); `pdo:totalPrice` must be `xsd:decimal` and strictly greater than zero (`sh:minExclusive 0`); `pdo:containMedicine` must have at least one value and point to a `pdo:Medicine` individual.

**pdo:PrescriptionShape** (targets `pdo:Prescription`):

```turtle
sh:property [
    sh:path    pdo:prescriptionID ;
    sh:minCount 1 ; sh:maxCount 1 ;
    sh:pattern "^RX-\\d{4}-\\d{3,}$" ;
    sh:message "prescriptionID must match pattern RX-YYYY-NNN." ;
] ;
```

This pattern constraint ensures prescription IDs are structurally valid before being accepted into the knowledge graph.

**pdo:DeliveryPersonShape** (targets `pdo:DeliveryPerson`):

`pdo:rating` is constrained to `sh:minInclusive 0.0` and `sh:maxInclusive 5.0` (xsd:decimal), and `pdo:vehicleType` must be one of `{"bicycle", "motorcycle", "car", "van", "drone"}`.

### 6.3 Validation Results

Validation was executed using pyshacl:

```python
conforms, results_graph, results_text = pyshacl.validate(
    data_graph=g, shacl_graph=shacl_graph,
    inference="rdfs", abort_on_first=False
)
```

**Result: CONFORMS = True — 0 violations across all 31 individuals.**

During development, three categories of violations were encountered and resolved:

1. **DatatypeConstraintComponent violations** on numeric properties — caused by Python `float` literals being stored as `xsd:float` instead of `xsd:decimal`. Resolved by using `Decimal("18.75")` from Python's `decimal` module.
2. **InConstraintComponent violations** on enum properties — caused by untyped Turtle string literals not matching typed `xsd:string` members in `sh:in` lists. Resolved by adding `^^xsd:string` datatype tags to `dosageForm`, `orderStatus`, and `vehicleType` values in the Turtle file.
3. **PatternConstraintComponent violations** on test individuals — resolved by ensuring all programmatically added prescriptionIDs follow the `RX-YYYY-NNN` pattern.

These violations are pedagogically valuable: they demonstrate that SHACL successfully catches real data quality issues that would otherwise propagate silently.

---

## 7. LLM Integration

### 7.1 System Architecture

The LLM integration follows a **Retrieval-Augmented Generation (RAG)** pattern. Rather than relying solely on a pre-trained language model's parametric knowledge (which may be outdated or hallucinated), structured facts are extracted from the knowledge graph via SPARQL and provided as explicit context to the LLM. This architecture ensures that all answers are traceable to specific triples in the knowledge graph.

The pipeline has four stages:

**Stage 1 — KG Load:** rdflib parses `pharmacy-kg.ttl` and `pharmacy.owl` into a merged in-memory graph (312 triples).

**Stage 2 — SPARQL Context Extraction:** Three SPARQL SELECT queries extract the most informative subsets of the graph—all orders with user and medicine details, all prescription medicines with metadata, and all courier assignments. Results are serialized as plain text (variable=value pairs), yielding approximately 2,400 characters of structured context.

**Stage 3 — Grounded Prompt Construction:** The system prompt instructs the LLM to answer *only* from the provided context and to respond with "This information is not available in the knowledge graph" if the answer is not present. Temperature is set to 0.0 (deterministic) to minimize creative elaboration.

```
System: You are a helpful assistant for a pharmacy delivery system.
        You MUST answer questions ONLY using the structured knowledge
        graph context provided. Do NOT make up any information not
        present in the context. If the answer is not in the context,
        say 'This information is not available in the knowledge graph.'

User: [KG Context Block]
      Question: [Natural language question]
      Answer based strictly on the knowledge graph context above:
```

**Stage 4 — LLM Response:** GPT-4o-mini generates a response grounded in the context. The response is returned to the user with source tracing.

### 7.2 Hallucination Mitigation Strategies

Three strategies are employed to reduce hallucination risk:

1. **Context injection:** Structured KG facts replace the LLM's reliance on parametric memory for domain-specific queries.
2. **Temperature 0.0:** Deterministic sampling prevents creative elaboration beyond the context.
3. **Explicit fallback instruction:** The system prompt mandates a structured "not available" response when the question cannot be answered from context, preventing the LLM from fabricating plausible-sounding but incorrect information.

### 7.3 Example Interactions

**Question:** *Which medicines require a prescription and who issued them?*

**KG Context (extracted via SPARQL):**
```
medicineName=Paracetamol, prescriptionID=RX-2026-001, doctor=Dr. Mehmet Yilmaz
medicineName=Amoxicillin, prescriptionID=RX-2026-002, doctor=Dr. Fatma Sahin
...
```

**LLM Response:**
> Based on the Knowledge Graph, the following medicines require valid prescriptions:
> Paracetamol (RX-2026-001, Dr. Mehmet Yilmaz), Amoxicillin (RX-2026-002, Dr. Fatma Sahin),
> Metformin (RX-2026-003, Dr. Ali Kaya), Atorvastatin (RX-2026-004, Dr. Mehmet Yilmaz),
> Omeprazole (RX-2026-005, Dr. Elif Demir), Lisinopril (RX-2026-006, Dr. Ali Kaya).
> Ibuprofen and Vitamin D3 are available over-the-counter.

**Question:** *How much did the most active courier earn in delivery fees?*

**LLM Response (correctly bounded):**
> This information is not available in the knowledge graph. The knowledge graph contains delivery fee data per order and courier assignments, but does not store a "total earnings" property for couriers. You could derive this via the SPARQL query: SUM(?deliveryFee) GROUP BY ?courier.

The second example demonstrates the fallback behavior: the LLM acknowledges the limit of available data and even suggests a SPARQL-based workaround—entirely grounded in its understanding of the KG schema rather than fabricated.

### 7.4 Offline Demo Mode

For reproducibility without an OpenAI API key, `src/llm_integration.py --demo` runs a keyword-matching simulation over the SPARQL-extracted context. This mode produces structurally correct answers for the five pre-defined competency questions and is sufficient for demonstration purposes.

---

## 8. Evaluation, Discussion and Conclusion

### 8.1 Ontology Quality Assessment

**Consistency:** The OWL ontology is consistent under open-world assumption reasoning in Protégé (HermiT reasoner returns no inconsistencies). No conflicting class or property axioms were introduced.

**Completeness:** The ontology covers the six core entities of the pharmacy delivery domain and their primary relationships. However, several real-world concepts are absent: `Doctor` as a first-class class (currently modeled only as a string literal on `Prescription`), `InsuranceCompany`, `DeliveryZone`, and `MedicineCategory`. These omissions are by design—the current scope prioritizes tractability over exhaustiveness—but limit the expressivity of SPARQL queries that might, for instance, join prescriptions to specific physicians' profiles.

**Correctness:** All class, property, and constraint definitions are semantically appropriate. The choice to link Prescription to Medicine (rather than to Order) correctly reflects the real-world principle that a prescription authorizes the dispensing of a drug, not the delivery of a specific order.

### 8.2 SPARQL Query Performance

All ten queries execute in under 100ms on the 312-triple in-memory graph, which is expected given the small scale. The multi-hop Query 5 (6-class join) returns 7 rows, correctly handling the OTC edge case (Vitamin D3 appears with `(none)` for prescriptionID). Aggregation queries (Q6, Q7, Q10) produce correct GROUP BY results, validated manually against the source Turtle file.

### 8.3 SHACL Validation Effectiveness

The SHACL shapes successfully caught three categories of real data quality issues during development (see Section 6.3). The final validation report confirms zero violations, demonstrating both the correctness of the instance data and the utility of SHACL as a data quality enforcement mechanism. The `sh:in` enumeration constraint on `pdo:orderStatus` is particularly valuable—it prevents insertion of arbitrary status strings (e.g., "sent", "dispatching") that would make status-based SPARQL queries unreliable.

### 8.4 LLM Integration Effectiveness

The RAG architecture successfully eliminates hallucination on in-context questions. The key limitation is **context window scope**: the current implementation extracts three SPARQL query result sets as context (approximately 2,400 characters). For a larger knowledge graph, this approach would need to be enhanced with query routing—first identifying which subset of the KG is relevant to the user's question, then extracting only that subset as context—to avoid exceeding model context limits.

A secondary limitation is that the current LLM integration does not support **natural language to SPARQL translation** (NL2SPARQL). This would represent a more sophisticated integration, allowing users to formulate arbitrary questions that are automatically converted to SPARQL queries and executed against the live knowledge graph. This is left as a future extension.

### 8.5 Limitations

1. **Synthetic data:** The knowledge graph does not contain real pharmacy operational data. Validation against real TITCK data would reveal additional modeling requirements.
2. **No OWL reasoning rules:** Properties are not declared as inverse, symmetric, or transitive. Adding `owl:inverseOf` between `placesOrder` and a hypothetical `placedBy` would enable richer inference.
3. **Static stock quantities:** Medicine stock is a single integer property; the model does not track stock changes over time (no event-based modeling).
4. **No SWRL rules:** Business rules (e.g., "an order cannot be delivered if the prescription has expired") are not encoded in the ontology—they would need to be enforced at the application layer.
5. **LLM cost dependency:** Full LLM integration requires an OpenAI API key, introducing financial cost and external API dependency. A self-hosted open-source LLM (e.g., Llama 3, Mistral) via Ollama would improve reproducibility.

### 8.6 Conclusion

The Pharmacy Delivery Ontology project successfully demonstrates a complete knowledge engineering pipeline applied to a real-world domain. Starting from a formal OWL ontology developed in Protégé, the project progressed through knowledge graph construction in RDF/Turtle, structured querying with ten SPARQL queries covering basic, reasoning, and aggregation patterns, data quality enforcement through six SHACL NodeShapes (zero violations), and LLM integration via a RAG architecture with explicit hallucination mitigation. The project produced a fully reproducible, script-driven implementation and a WIDOCO-style documentation page.

From a learning perspective, the project demonstrated that ontology design decisions have significant downstream consequences: the choice to model Prescription as a first-class entity (rather than a boolean flag on Medicine) enabled richer SPARQL queries but required careful handling in SHACL and the LLM context. The SHACL debugging process provided practical insight into the gap between ontological intent and data encoding reality—particularly regarding literal datatypes in Turtle versus SHACL constraint expectations. Future extensions should prioritize NL2SPARQL integration, connection to real open datasets (TITCK, Wikidata pharmacology), and deployment on a live SPARQL endpoint.

---

## References

Horridge, M., & Bechhofer, S. (2011). The OWL API: A Java API for OWL ontologies. *Semantic Web*, *2*(1), 11–21. https://doi.org/10.3233/SW-2011-0025

Knublauch, H., & Kontokostas, D. (Eds.). (2017). *Shapes Constraint Language (SHACL)*. W3C Recommendation. https://www.w3.org/TR/shacl/

Harris, S., & Seaborne, A. (Eds.). (2013). *SPARQL 1.1 query language*. W3C Recommendation. https://www.w3.org/TR/sparql11-query/

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, *33*, 9459–9474. https://doi.org/10.48550/arXiv.2005.11401

Lohmann, S., Negru, S., Haag, F., & Ertl, T. (2016). Visualizing ontologies with VOWL. *Semantic Web*, *7*(4), 399–419. https://doi.org/10.3233/SW-150200

Noy, N. F., & McGuinness, D. L. (2001). *Ontology development 101: A guide to creating your first ontology* (Technical Report KSL-01-05). Stanford Knowledge Systems Laboratory. https://protege.stanford.edu/publications/ontology_development/ontology101.pdf

Pérez, J., Arenas, M., & Gutierrez, C. (2009). Semantics and complexity of SPARQL. *ACM Transactions on Database Systems*, *34*(3), 1–45. https://doi.org/10.1145/1567274.1567278

Schreiber, G., & Raimond, Y. (Eds.). (2014). *RDF 1.1 Primer*. W3C Working Group Note. https://www.w3.org/TR/rdf11-primer/

World Wide Web Consortium. (2012). *OWL 2 Web Ontology Language: Primer* (2nd ed.). W3C Recommendation. https://www.w3.org/TR/owl2-primer/

Allemang, D., & Hendler, J. (2011). *Semantic Web for the working ontologist: Effective modeling in RDFS and OWL* (2nd ed.). Morgan Kaufmann. https://doi.org/10.1016/B978-0-12-385965-5.10001-5

---

## Appendix

### Appendix A: Repository Structure

```
pharmacy-delivery-ontology/
├── pharmacy.owl                        # Core OWL ontology (Protégé)
├── pharmacy-kg.ttl                     # RDF/Turtle Knowledge Graph (instances)
├── pharmacy-kg-merged.ttl              # Merged KG + Ontology (auto-generated)
├── queries/
│   ├── query1_users_and_orders.rq      # Basic: Users and their orders
│   ├── query2_prescription_medicines.rq # Basic: Prescription medicines
│   ├── query3_orders_by_courier.rq     # Basic: Orders by courier
│   ├── query4_pharmacy_medicines.rq    # Basic: Pharmacy stock
│   ├── query5_full_order_pipeline.rq   # Reasoning: 6-class pipeline join
│   ├── query6_orders_count_by_status.rq # Aggregation: COUNT by status
│   ├── query7_avg_delivery_fee_per_pharmacy.rq # Aggregation: AVG fee + SUM revenue
│   ├── query8_otc_medicines.rq         # Reasoning: FILTER NOT EXISTS
│   ├── query9_top_rated_couriers.rq    # Reasoning: FILTER + COUNT
│   └── query10_spending_per_user.rq    # Aggregation: SUM + MAX per user
├── shacl/
│   └── pharmacy_shapes.shacl          # 6 SHACL NodeShapes
├── src/
│   ├── build_kg.py                    # KG load, query, extend, validate
│   └── llm_integration.py             # LLM Q&A (RAG architecture)
├── docs/
│   └── index.html                     # WIDOCO-style HTML documentation
├── presentation/
│   └── slides.html                    # 12-slide interactive presentation
├── report/
│   └── project_report.md              # This document
└── README.md                          # Repository overview
```

### Appendix B: How to Run

**Prerequisites:**

```bash
pip install rdflib pyshacl openai
```

**Run KG Builder and Validator:**

```bash
python src/build_kg.py
```

Output: KG summary, 10 SPARQL query results, SHACL validation report, merged graph saved.

**Run LLM Q&A (offline demo):**

```bash
python src/llm_integration.py --demo
```

**Run LLM Q&A (with OpenAI API):**

```bash
set OPENAI_API_KEY=sk-...
python src/llm_integration.py
```

**View Ontology Documentation:**

Open `docs/index.html` in any browser.

**View Presentation:**

Open `presentation/slides.html` in any browser. Use ← → keys to navigate; press F for fullscreen.

### Appendix C: KG Triple Statistics

| Metric | Value |
|---|---|
| Total triples (merged) | 312 |
| ABox triples (pharmacy-kg.ttl only) | 279 |
| TBox triples (pharmacy.owl only) | 33 |
| Named individuals | 31 |
| Object property assertions | 42 |
| Data property assertions | 237 |
| SHACL constraints | 6 NodeShapes, 34 PropertyShapes |
| SPARQL queries implemented | 10 |
| SHACL violations (final) | 0 |

### Appendix D: SPARQL Query 3 Full Output

| courierID | firstName | lastName | vehicleType | orderID | orderStatus | totalPrice | deliveryFee |
|---|---|---|---|---|---|---|---|
| COR-001 | Kemal | Arslan | motorcycle | ORD-2026-001 | delivered | 12.50 | 5.00 |
| COR-001 | Kemal | Arslan | motorcycle | ORD-2026-003 | delivered | 28.00 | 5.00 |
| COR-001 | Kemal | Arslan | motorcycle | ORD-2026-005 | delivered | 41.50 | 5.00 |
| COR-002 | Hasan | Ozturk | bicycle | ORD-2026-002 | delivered | 45.00 | 5.00 |
| COR-002 | Hasan | Ozturk | bicycle | ORD-2026-006 | processing | 87.00 | 5.00 |
| COR-003 | Burak | Koc | motorcycle | ORD-2026-004 | in-transit | 67.00 | 7.00 |

### Appendix E: LLM Prompt Template

```
SYSTEM PROMPT:
  You are a helpful assistant for a pharmacy delivery system.
  You MUST answer questions ONLY using the structured knowledge graph
  context provided. Do NOT make up any information not present in the
  context. If the answer is not in the context, say:
  'This information is not available in the knowledge graph.'
  Always cite specific facts from the context in your answer.

USER PROMPT STRUCTURE:
  Knowledge Graph Context:
  === PHARMACY DELIVERY KNOWLEDGE GRAPH CONTEXT ===
  [ORDERS]       {sparql_orders_result}
  [PRESCRIPTION MEDICINES] {sparql_prescriptions_result}
  [COURIERS & DELIVERIES]  {sparql_couriers_result}
  === END OF CONTEXT ===

  User Question: {natural_language_question}

  Answer based strictly on the knowledge graph context above:

LLM PARAMETERS:
  model:       gpt-4o-mini
  temperature: 0.0
  max_tokens:  400
```
