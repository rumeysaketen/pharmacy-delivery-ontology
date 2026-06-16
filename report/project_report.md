# Pharmacy Delivery Ontology
## Knowledge Engineering and Ontologies – Term Project Report

**Course:** Knowledge Engineering and Ontologies  
**Submission Deadline:** June 17, 2026  
**GitHub Repository:** https://github.com/rumeysaketen/pharmacy-delivery-ontology  
**WIDOCO Documentation:** https://rumeysaketen.github.io/pharmacy-delivery-ontology/docs/

---

## Executive Summary

This project presents the **Pharmacy Delivery Ontology (PDO)**, a formal OWL ontology designed to model the domain of online pharmacy delivery systems. The ontology captures the key entities—users, medicines, orders, pharmacies, prescriptions, and delivery personnel—along with their relationships and constraints. The accompanying knowledge graph, encoded in RDF/Turtle, instantiates 20+ individuals representing a realistic delivery scenario. Data quality is enforced through six SHACL NodeShapes, and the graph is queryable via five SPARQL queries ranging from simple lookups to complex multi-hop traversals. A Python script automates loading, querying, programmatic extension, and SHACL validation of the graph.

---

## 1. Project Description

### 1.1 Problem Domain

Online pharmacy delivery platforms have become increasingly important in modern healthcare infrastructure, particularly following the COVID-19 pandemic. These platforms allow patients to order both prescription and over-the-counter (OTC) medications and receive them at home, often within hours.

The domain involves multiple stakeholders with complex interdependencies:
- **Users (customers)** who place medication orders
- **Medicines** that may or may not require prescriptions
- **Doctors** who issue prescriptions
- **Pharmacies** that stock and prepare orders
- **Couriers** who deliver orders to customers

Managing these relationships formally—ensuring data consistency, enabling complex queries, and supporting interoperability—motivates the use of ontological modeling.

### 1.2 Objectives

1. Design a formal OWL ontology capturing the pharmacy delivery domain
2. Instantiate a knowledge graph with realistic sample data (RDF/Turtle)
3. Express meaningful SPARQL queries to retrieve actionable information
4. Define SHACL shapes to enforce data integrity constraints
5. Develop a Python script to automate KG operations

### 1.3 Scope and Limitations

**In scope:**
- Online pharmacy delivery workflow
- Prescription validation requirement
- Courier assignment and delivery tracking
- Medicine stock management

**Out of scope:**
- Real-time GPS tracking
- Payment processing
- Insurance billing
- Hospital system integration

---

## 2. Ontology Design

### 2.1 Classes

The ontology defines **6 core classes**, all subclasses of `owl:Thing`:

| Class | IRI | Description |
|---|---|---|
| `User` | `pdo:User` | Customer who places medication orders |
| `Medicine` | `pdo:Medicine` | Pharmaceutical product |
| `Order` | `pdo:Order` | Purchase request containing medicines |
| `Pharmacy` | `pdo:Pharmacy` | Licensed pharmacy establishment |
| `Prescription` | `pdo:Prescription` | Doctor-issued authorization |
| `DeliveryPerson` | `pdo:DeliveryPerson` | Courier responsible for delivery |

**Base namespace:** `http://www.semanticweb.org/rumey/ontologies/2026/3/untitled-ontology-3#`

### 2.2 Object Properties

Five object properties define the relationships between classes:

| Property | Domain | Range | Description |
|---|---|---|---|
| `placesOrder` | User | Order | A user places one or more orders |
| `containMedicine` | Order | Medicine | An order contains one or more medicines |
| `deliveredBy` | Order | DeliveryPerson | An order is assigned to a courier |
| `providedBy` | Medicine | Pharmacy | A medicine is stocked by a pharmacy |
| `requiresPrescription` | Medicine | Prescription | A medicine requires a valid prescription |

### 2.3 Data Properties

Over 20 data properties annotate individuals with typed literal values. Key examples:

- `pdo:firstName`, `pdo:lastName`, `pdo:email` → xsd:string (User)
- `pdo:medicineName`, `pdo:brandName`, `pdo:dosageForm` → xsd:string (Medicine)
- `pdo:price`, `pdo:totalPrice` → xsd:decimal
- `pdo:stockQuantity` → xsd:integer
- `pdo:issueDate`, `pdo:dateOfBirth` → xsd:date
- `pdo:orderDate`, `pdo:deliveryDate` → xsd:dateTime
- `pdo:orderID`, `pdo:prescriptionID`, `pdo:courierID` → xsd:string (Functional)

### 2.4 Design Decisions

- **No class hierarchy** was introduced beyond the six core classes to keep the ontology accessible and focused. Future versions could introduce `PrescriptionMedicine` and `OTCMedicine` as subclasses of `Medicine`.
- **Functional properties** (orderID, prescriptionID, courierID) ensure unique identifiers per individual.
- The **`requiresPrescription`** property links Medicine to Prescription rather than to a boolean flag, enabling richer prescription metadata to be captured.

---

## 3. Data Acquisition and Knowledge Graph Construction

### 3.1 Data Sources

The knowledge graph instances are **synthetic but realistic**, designed to represent a plausible Turkish online pharmacy delivery scenario. Instance data was created manually to cover:

- 5 users (Ayse, Mehmet, Zeynep, Ahmet, Fatma) in Istanbul, Ankara, and Izmir
- 8 medicines including both prescription-only (Amoxicillin, Metformin, Atorvastatin, Lisinopril) and OTC (Ibuprofen, VitaminD)
- 3 pharmacies across three cities
- 6 prescriptions issued by three doctors
- 3 couriers with different vehicle types
- 6 orders in various statuses (delivered, in-transit, processing)

### 3.2 Knowledge Graph Statistics

| Entity | Count |
|---|---|
| Users | 5 |
| Medicines | 8 |
| Orders | 6 |
| Pharmacies | 3 |
| Prescriptions | 6 |
| DeliveryPersons | 3 |
| **Total individuals** | **31** |

### 3.3 Construction Method

The knowledge graph was encoded manually in **RDF/Turtle** format (`pharmacy-kg.ttl`), following the classes and properties defined in `pharmacy.owl`. The Python script `src/build_kg.py` uses **rdflib** to load and merge both files, demonstrating programmatic KG extension with a new individual (User `pdo:Ali`).

---

## 4. SPARQL Queries

Five SPARQL 1.1 queries were designed to retrieve meaningful information from the knowledge graph.

### Query 1 – Users and their Orders
**Purpose:** List all users with their placed orders, including status and price.  
**Technique:** Basic graph pattern + BIND for local name extraction.

### Query 2 – Prescription Medicines
**Purpose:** Retrieve all medicines linked to a prescription with full prescription metadata.  
**Technique:** Mandatory join on `requiresPrescription` + OPTIONAL for metadata.

### Query 3 – Orders by Courier
**Purpose:** Group delivered orders by courier, showing vehicle type and fees.  
**Technique:** Join across `deliveredBy` + OPTIONAL for courier details.

### Query 4 – Pharmacy Medicine Stock
**Purpose:** List all medicines stocked per pharmacy with price and stock quantity.  
**Technique:** Join on `providedBy` + OPTIONAL for quantities.

### Query 5 – Full Order Pipeline (Complex)
**Purpose:** Traverse the complete chain User → Order → Medicine → Prescription → Pharmacy → Courier.  
**Technique:** Multi-hop OPTIONAL pattern covering all 6 classes in a single query.

### Sample Result (Query 5, simplified)

| userFirstName | orderID | medicineName | prescriptionID | pharmacyName | courierFirstName | totalPrice |
|---|---|---|---|---|---|---|
| Ayse | ORD-2026-001 | Paracetamol | RX-2026-001 | Güven Eczanesi | Kemal | 12.50 |
| Mehmet | ORD-2026-002 | Amoxicillin | RX-2026-002 | Güven Eczanesi | Hasan | 45.00 |
| Zeynep | ORD-2026-003 | Metformin | RX-2026-003 | Sağlık Eczanesi | Kemal | 28.00 |

---

## 5. SHACL Validation

### 5.1 Overview

Six SHACL NodeShapes (`pharmacy_shapes.shacl`) enforce data quality:

| Shape | Target Class | Key Constraints |
|---|---|---|
| `pdo:UserShape` | `pdo:User` | firstName, lastName required; email regex validation |
| `pdo:OrderShape` | `pdo:Order` | orderID required; orderStatus enum; totalPrice > 0; ≥1 medicine |
| `pdo:MedicineShape` | `pdo:Medicine` | medicineName required; providedBy ≥1; price > 0; dosageForm enum |
| `pdo:PrescriptionShape` | `pdo:Prescription` | prescriptionID pattern (RX-YYYY-NNN); issueDate required |
| `pdo:PharmacyShape` | `pdo:Pharmacy` | pharmacyName and pharmacyID required |
| `pdo:DeliveryPersonShape` | `pdo:DeliveryPerson` | courierID required; vehicleType enum; rating 0–5 |

### 5.2 Validation Results

Running `python src/build_kg.py` with **pyshacl** validates the merged graph. All 31 core individuals conform to their respective shapes. The programmatically added demo individual (Ali/Order007) also passes validation.

### 5.3 Constraint Examples

**Email pattern on User:**
```
sh:pattern "^[\\w._%+\\-]+@[\\w.\\-]+\\.[a-zA-Z]{2,}$"
```

**OrderStatus enumeration on Order:**
```
sh:in ( "pending" "processing" "shipped" "in-transit" "delivered" "cancelled" )
```

**PrescriptionID format:**
```
sh:pattern "^RX-\\d{4}-\\d{3,}$"
```

---

## 6. Evaluation and Discussion

### 6.1 Strengths

- **Complete coverage** of the delivery workflow from order placement to delivery
- **Prescription validation** modeled as a first-class relationship, not a boolean flag
- **Extensible design**: new classes (e.g., `Doctor`, `InsurancePlan`) can be added without breaking existing properties
- **Strict SHACL constraints** prevent invalid data from entering the graph
- **Python automation** makes the KG reproducible and testable

### 6.2 Limitations

- The ontology does not model **temporal constraints** (e.g., prescription expiration enforcement in SPARQL)
- No **OWL reasoning rules** (e.g., inverse properties, transitivity) were leveraged
- The **knowledge graph is synthetic**; integration with a real pharmacy database would require ETL pipelines
- WIDOCO documentation was implemented manually as HTML; true WIDOCO requires the Java tool

### 6.3 Future Work

1. Add `Doctor` and `InsuranceCompany` classes with appropriate properties
2. Introduce OWL restrictions (e.g., every Order must have at least one Medicine via `owl:minCardinality`)
3. Integrate real open data sources (e.g., Turkish TITCK medicine database via SPARQL federation)
4. Add SWRL rules for automatic order status inference
5. Deploy on a triple store (Apache Jena Fuseki) with a SPARQL endpoint

---

## 7. Conclusion

The Pharmacy Delivery Ontology successfully models the key entities and relationships of an online pharmacy delivery system. Starting from the two foundational files (`pharmacy.owl` and `README.md`), the project was expanded into a complete knowledge engineering submission including a rich RDF/Turtle knowledge graph, five SPARQL queries, six SHACL validation shapes, a Python automation script, and WIDOCO-style HTML documentation. The ontology is sufficiently general to be adapted for real pharmacy delivery platforms while remaining tractable and well-documented.

---

## References

Horridge, M., & Bechhofer, S. (2011). The OWL API: A Java API for OWL Ontologies. *Semantic Web*, 2(1), 11–21. https://doi.org/10.3233/SW-2011-0025

Knublauch, H., & Kontokostas, D. (Eds.). (2017). *Shapes Constraint Language (SHACL)*. W3C Recommendation. https://www.w3.org/TR/shacl/

Harris, S., & Seaborne, A. (Eds.). (2013). *SPARQL 1.1 Query Language*. W3C Recommendation. https://www.w3.org/TR/sparql11-query/

Lohmann, S., Negru, S., Haag, F., & Ertl, T. (2015). VOWL 2: User-Oriented Visualization of Ontologies. *Journal on Data Semantics*, 5(3), 1–15. https://doi.org/10.1007/s13740-015-0042-8

Noy, N. F., & McGuinness, D. L. (2001). *Ontology Development 101: A Guide to Creating Your First Ontology* (Technical Report KSL-01-05). Stanford Knowledge Systems Laboratory.

Pérez, J., Arenas, M., & Gutierrez, C. (2009). Semantics and Complexity of SPARQL. *ACM Transactions on Database Systems*, 34(3), 1–45. https://doi.org/10.1145/1567274.1567278

World Health Organization. (2021). *WHO model list of essential medicines* (22nd ed.). Geneva: World Health Organization.
