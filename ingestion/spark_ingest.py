"""PySpark batch ingestion job for large-scale document processing."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, List


def _require_pyspark() -> Any:
    try:
        from pyspark.sql import SparkSession  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "pyspark is required for spark ingestion. Install with: pip install pyspark"
        ) from exc
    return SparkSession


def chunk_text_spark(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    from api.ingestion.chunker import chunk_text

    return [c.chunk_text for c in chunk_text(text, chunk_size=chunk_size, overlap=overlap)]


def map_partition_to_rows(partition: Iterator[Dict[str, Any]], embedding_model_name: str) -> Iterator[Dict[str, Any]]:
    """mapPartitions worker: chunk documents and prepare bulk-write rows."""
    from api.embeddings.providers import DummyEmbeddingProvider

    provider = DummyEmbeddingProvider()
    for record in partition:
        tenant_id = record.get("tenant_id")
        document_id = record.get("document_id")
        content = record.get("content", "")
        chunks = chunk_text_spark(content)
        embeddings = provider.embed_documents(chunks)
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            yield {
                "tenant_id": tenant_id,
                "document_id": document_id,
                "chunk_index": index,
                "chunk_text": chunk,
                "embedding": embedding,
                "embedding_model": embedding_model_name,
                "metadata": record.get("metadata", {}),
            }


def run_spark_ingest(input_path: str, embedding_model_name: str = "dummy") -> int:
    """Run batch ingestion and return prepared row count."""
    SparkSession = _require_pyspark()
    spark = SparkSession.builder.appName("rag-spark-ingest").getOrCreate()

    # Broadcast placeholder for future model/service configuration.
    model_name = spark.sparkContext.broadcast(embedding_model_name)

    df = spark.read.json(input_path)

    def _partition_fn(partition):
        return map_partition_to_rows(partition, model_name.value)

    prepared = df.rdd.mapPartitions(_partition_fn)
    count = prepared.count()
    spark.stop()
    return count


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="PySpark batch ingestion")
    parser.add_argument("input_path", help="Local or S3-style JSON path")
    parser.add_argument("--embedding-model", default="dummy")
    args = parser.parse_args()
    total = run_spark_ingest(args.input_path, embedding_model_name=args.embedding_model)
    print(json.dumps({"prepared_rows": total}))


if __name__ == "__main__":
    main()
