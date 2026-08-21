import os
import boto3
from botocore.client import Config

class StorageService:
    def __init__(self):
        self.endpoint_url = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET", "algolyra-documents")
        
        # Initialize boto3 S3 client with fast timeout for offline fallback
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(
                signature_version="s3v4",
                connect_timeout=0.5,
                read_timeout=0.5,
                retries={"max_attempts": 0}
            ),
            region_name="us-east-1"
        )
        
        # Memory storage fallback for in-memory unit tests
        self._in_memory_store = {}

    def upload_file(self, file_bytes: bytes, object_key: str, content_type: str = "application/pdf") -> str:
        """Uploads file payload to S3/MinIO bucket, local disk storage, and memory store."""
        # 1. Always save to local disk storage directory
        try:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "claim-documents")
            file_path = os.path.join(base_dir, object_key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            pass

        # 2. Register file object in Supabase Storage Postgres database (storage.objects)
        try:
            import uuid
            import json
            from db.session import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO storage.objects (id, bucket_id, name, metadata, created_at, updated_at)
                        VALUES (:id, :bucket_id, :name, :metadata, NOW(), NOW())
                        ON CONFLICT (bucket_id, name) DO UPDATE SET updated_at = NOW(), metadata = :metadata;
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "bucket_id": "claim-documents",
                        "name": object_key,
                        "metadata": json.dumps({"mimetype": content_type, "size": len(file_bytes)}),
                    }
                )
                conn.commit()
        except Exception:
            pass

        # 3. Upload to S3/MinIO bucket if available
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type
            )
        except Exception:
            self._in_memory_store[object_key] = file_bytes
            
        return object_key

    def get_signed_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generates a short-lived presigned URL for document access."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception:
            return f"{self.endpoint_url}/{self.bucket_name}/{object_key}?presigned_token=local_test_token"

storage_service = StorageService()
