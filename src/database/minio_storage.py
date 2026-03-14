import io
from typing import List
from minio import Minio
from src.core.base import BaseComponent


from src.config.configs import MINIO_CONFIG
from src.utils.logger import logger


class MinIOStorage(BaseComponent):
    """
    MinIO Object Storage client.
    Uses the minio Python library directly (no Airflow provider).
    Connection info is loaded from MINIO_CONFIG.
    """

    def __init__(self):
        super().__init__(name="minio_storage", config=MINIO_CONFIG)
        self.default_bucket = MINIO_CONFIG["bucket"]

        self.client = Minio(
            endpoint=MINIO_CONFIG["endpoint"],
            access_key=MINIO_CONFIG["access_key"],
            secret_key=MINIO_CONFIG["secret_key"],
            secure=MINIO_CONFIG["secure"],
            region=MINIO_CONFIG["region"]
        )
        logger.info("MinIO client created for endpoint: %s", MINIO_CONFIG["endpoint"])
        self.ping()

    def ping(self) -> bool:
        """
        Check connection to MinIO by listing buckets.
        Returns True if successful, False otherwise.
        """
        try:
            self.client.list_buckets()
            logger.info("MinIO connection successful.")
            return True
        except Exception as e:
            logger.error("Failed to connect to MinIO: %s", e)
            return False

    # ------------------------------------------------------------------ #
    #  Core Methods                                                       #
    # ------------------------------------------------------------------ #

    def list_buckets(self) -> List[str]:
        """Return a list of all bucket names."""
        buckets = self.client.list_buckets()
        return [bucket.name for bucket in buckets]

    def list_objects(self, bucket_name: str, prefix: str = "") -> List[str]:
        """Return a list of object names in *bucket_name*."""
        objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]

    def download_object(self, bucket_name: str, object_name: str) -> bytes:
        """Download an object and return its content as bytes (kept in RAM)."""
        response = None
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            logger.info(
                "Downloaded '%s/%s' (%d bytes)", bucket_name, object_name, len(data)
            )
            return data
        except Exception as e:
            logger.error("Error downloading '%s/%s': %s", bucket_name, object_name, e)
            raise e
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def upload_object(
        self, bucket_name: str, object_name: str, data: bytes
    ) -> bool:
        """Upload bytes from RAM to MinIO."""
        try:
            stream = io.BytesIO(data)
            self.client.put_object(
                bucket_name,
                object_name,
                data=stream,
                length=len(data),
            )
            logger.info(
                "Uploaded '%s/%s' (%d bytes)", bucket_name, object_name, len(data)
            )
            return True
        except Exception as e:
            logger.error("Error uploading '%s/%s': %s", bucket_name, object_name, e)
            return False

    # ------------------------------------------------------------------ #
    #  BaseComponent interface                                            #
    # ------------------------------------------------------------------ #

    def run(self):
        """Verify connectivity by listing buckets."""
        buckets = self.list_buckets()
        logger.info("MinIO connected — buckets: %s", buckets)
        self.status = "connected"
        return buckets
