# DPDP Compass Corpus Capacity

## Current Corpus

| Metric | Value |
|---|---:|
| PDF documents | 5 |
| Total pages | 68 |
| Extracted characters | 191,402 |
| Estimated tokens | 47,851 |
| Estimated embedding storage | 280.38 MiB |

## 1,000-Page Projection

| Metric | Estimate |
|---|---:|
| Pages | 1,000 |
| Characters | 2,814,735 |
| Estimated tokens | 703,684 |
| Estimated embedding storage | 4.03 GiB |

## Estimation Method

Token estimation uses approximately 4 characters per token.

Embedding storage assumes 1,536 dimensions with 4 bytes per float32 value.

These figures are estimates generated from the current corpus using:

`uv run python scripts/dataset_report.py --full-pages 1000`

## Capacity Questions

### 1. How large is the current corpus?

The current corpus contains 5 PDFs totaling 68 pages, with approximately 47,851 estimated tokens.

### 2. What would 1,000 pages require?

A 1,000-page corpus is estimated at approximately 703,684 tokens and 4.03 GiB of embedding storage.

### 3. What are the main scaling considerations?

The main considerations are document storage, PDF text extraction, chunking, embedding generation, vector database storage, ingestion time, and API/provider costs.

### 4. What are the current gaps?

The current corpus does not yet include the broader target material such as MeitY FAQs, additional official explainers, SPDI Rules 2011, Information Technology Act material, PIB explainers, Data Protection Board notices, and other material needed to reach a 1,000+ page corpus.

## Notes

The capacity figures are planning estimates, not measured production storage requirements. Actual storage will depend on chunk size, overlap, embedding model dimensions, metadata, indexing strategy, and vector database overhead.
