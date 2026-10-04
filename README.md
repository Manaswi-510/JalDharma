# Jal Dharma AI
### AI-Enabled Water Demand Prediction and Equitable Allocation System.

Jal Dharma AI is an AI-driven water management system designed to predict future water demand, model water distribution networks, and allocate limited water resources in an equitable and physically feasible manner.

The system combines **Machine Learning, GIS, Graph Algorithms, optimization, and Water Justice Metrics** to support data-driven water allocation under conditions such as drought, increasing demand, and infrastructure failures.

---

## Overview

Water scarcity does not affect all communities equally. A simple proportional allocation of available water may overlook differences in population, historical shortages, accessibility, vulnerability, and network constraints.

Jal Dharma AI addresses this problem through an end-to-end pipeline:

**Predict → Model → Calculate → Optimize → Measure → Visualize**

The system:

- Predicts future water demand using historical demand and environmental factors.
- Represents the physical water network as a graph.
- Calculates how much water can actually reach each village.
- Optimizes allocation under limited water availability.
- Considers village-level priority and vulnerability.
- Measures allocation fairness and water shortages.
- Visualizes the water network, demand, allocation, and justice metrics through a dashboard.
- Allows simulation of different water-scarcity scenarios.

---

## Key Objectives

1. Predict future water demand for individual villages.
2. Model water sources, tanks, pipelines, and villages as a spatial network.
3. Calculate physically reachable water using maximum-flow algorithms.
4. Allocate limited water using mathematical optimization.
5. Incorporate population, historical shortage, accessibility, and vulnerability into allocation priorities.
6. Quantify fairness using water justice metrics.
7. Compare different allocation strategies.
8. Simulate scenarios such as drought, population growth, and pipeline failure.
9. Provide an interactive GIS-based decision-support dashboard.

---

## System Architecture

```text
                    ┌─────────────────────┐
                    │    Data Sources     │
                    │                     │
                    │ Demand | Weather    │
                    │ Population | GIS    │
                    │ Water Infrastructure│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Data Processing   │
                    │ Cleaning & EDA      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   PostgreSQL +      │
                    │      PostGIS        │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
      ┌──────────────────┐          ┌──────────────────┐
      │ Demand Prediction│          │  GIS Water       │
      │                  │          │  Network         │
      │ ML / Time Series │          │                  │
      └────────┬─────────┘          └────────┬─────────┘
               │                             │
               ▼                             ▼
      ┌─────────────────────────────────────────────┐
      │              Graph Representation           │
      │                 NetworkX                    │
      └──────────────────────┬──────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    Max-Flow      │
                    │ Water Availability│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Optimization     │
                    │      LP          │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Equitable Water  │
                    │    Allocation    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Water Justice    │
                    │    Metrics       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ GIS + Dashboard  │
                    └──────────────────┘