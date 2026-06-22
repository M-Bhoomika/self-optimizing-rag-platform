# PySpark Batch Ingestion

Batch ingestion job for processing large JSON document corpora with PySpark.

## Input format

JSON records with fields:

```json
{
  "tenant_id": "tenant-1",
  "document_id": "doc-1",
  "content": "Document body...",
  "metadata": {"source": "s3://bucket/path"}
}
```

## Job behavior

1. Read JSON from a local path or S3-style path (`s3a://bucket/prefix`).
2. Chunk documents using the shared Python chunker.
3. Generate embeddings via the configured embedding provider abstraction.
4. Emit rows prepared for PostgreSQL/Chroma bulk writes using `mapPartitions`.

A broadcast variable carries the embedding model name (placeholder for future
model/service configuration).

## Run

```bash
pip install pyspark

spark-submit \
  --master local[*] \
  ingestion/spark_ingest.py /path/to/documents.json

# S3-style path example (requires Hadoop/S3 configs):
spark-submit ingestion/spark_ingest.py s3a://my-bucket/documents/
```

## Output

The job prints a JSON summary with `prepared_rows`. Persisting rows to Postgres
or ChromaDB is a follow-up step (bulk COPY / batch upsert).

No performance numbers are included here — measure throughput on your cluster.
