# Pharmacy Delivery Ontology

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Project Description

This project presents a **Pharmacy Delivery Ontology (PDO)** developed as a term project for the *Knowledge Engineering and Ontologies* course. The ontology formally models the domain of online pharmacy delivery systems, covering all key entities and their relationships from order placement to doorstep delivery.

## Domain Overview

Online pharmacy delivery platforms allow customers to order prescription and over-the-counter medications and receive them at home. The system involves multiple stakeholders (users, pharmacists, couriers, doctors) and complex workflows (prescription validation, order processing, delivery tracking).

## Ontology Concepts

| Class | Description |
|---|---|
| `User` | A customer who places medication orders |
| `Medicine` | A pharmaceutical product (prescription or OTC) |
| `Order` | A request to purchase and deliver medications |
| `Pharmacy` | A licensed pharmacy that stocks and dispatches medicines |
| `Prescription` | A doctor-issued authorization for specific medications |
| `DeliveryPerson` | A courier responsible for delivering orders |

## Object Properties

| Property | Domain | Range | Description |
|---|---|---|---|
| `placesOrder` | User | Order | User places an order |
| `containMedicine` | Order | Medicine | Order contains a medicine |
| `deliveredBy` | Order | DeliveryPerson | Order is delivered by a courier |
| `providedBy` | Medicine | Pharmacy | Medicine is stocked by a pharmacy |
| `requiresPrescription` | Medicine | Prescription | Medicine needs a valid prescription |

## Repository Structure

```
pharmacy-delivery-ontology/
├── pharmacy.owl                  # Core OWL ontology (Protégé)
├── pharmacy-kg.ttl               # RDF/Turtle Knowledge Graph (instances)
├── queries/
│   ├── query1_users_and_orders.rq
│   ├── query2_prescription_medicines.rq
│   ├── query3_orders_by_courier.rq
│   ├── query4_pharmacy_medicines.rq
│   └── query5_full_order_pipeline.rq
├── shacl/
│   └── pharmacy_shapes.shacl     # SHACL validation shapes
├── src/
│   └── build_kg.py               # Python: load, query & validate KG
├── docs/
│   └── index.html                # Ontology documentation (WIDOCO-style)
└── README.md
```

## SPARQL Queries

| # | File | Description |
|---|---|---|
| 1 | `query1_users_and_orders.rq` | List all users and their placed orders |
| 2 | `query2_prescription_medicines.rq` | Medicines that require a prescription |
| 3 | `query3_orders_by_courier.rq` | Orders assigned to each courier |
| 4 | `query4_pharmacy_medicines.rq` | Medicines stocked per pharmacy |
| 5 | `query5_full_order_pipeline.rq` | Full pipeline: User → Order → Medicine → Pharmacy → Courier |

## SHACL Validation

Six SHACL NodeShapes enforce data quality:
- **UserShape** – firstName, lastName, email (with regex), phone
- **OrderShape** – orderID, orderStatus (enum), totalPrice > 0, ≥1 medicine
- **MedicineShape** – medicineName, providedBy, price > 0, stockQuantity ≥ 0
- **PrescriptionShape** – prescriptionID (pattern `RX-YYYY-NNN`), issueDate, doctor
- **PharmacyShape** – pharmacyName, pharmacyID, city
- **DeliveryPersonShape** – courierID, vehicleType (enum), rating 0–5

## Setup & Usage

### Requirements

```bash
pip install rdflib pyshacl
```

### Run the KG Builder & Validator

```bash
python src/build_kg.py
```

This script will:
1. Load `pharmacy.owl` + `pharmacy-kg.ttl`
2. Print a summary of all class instances
3. Execute all 5 SPARQL queries
4. Add a demo individual programmatically
5. Validate the graph against SHACL shapes
6. Save the merged graph as `pharmacy-kg-merged.ttl`

## Example Instance

```
Ayse (User) 
  → places Order001
      → contains Paracetamol (Medicine, 500mg tablet, 12.50 TL)
          → requiresPrescription Prescription123 (RX-2026-001, issued by Dr. Mehmet Yilmaz)
          → providedBy PharmacyA (Güven Eczanesi, Istanbul)
      → deliveredBy Courier1 (Kemal Arslan, motorcycle, rating 4.8)
```

## Team Members

| Name | Role |
|---|---|
| Rumeysa Keten | Ontology Design, KG Construction, SPARQL, SHACL |

## Links

- **GitHub Repository**: https://github.com/rumeysaketen/pharmacy-delivery-ontology
- **WIDOCO Documentation**: [*(GitHub Pages URL – to be added after deployment)*
](https://rumeysaketen.github.io/pharmacy-delivery-ontology/)
## References

- Horridge, M., & Bechhofer, S. (2011). The OWL API: A Java API for OWL Ontologies. *Semantic Web*, 2(1), 11–21.
- Knublauch, H., & Kontokostas, D. (2017). Shapes Constraint Language (SHACL). W3C Recommendation.
- Harris, S., & Seaborne, A. (2013). SPARQL 1.1 Query Language. W3C Recommendation.
- Lohmann, S., et al. (2015). WIDOCO: A Wizard for Documenting Ontologies. *ISWC*.
