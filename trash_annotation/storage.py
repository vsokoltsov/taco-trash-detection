from enum import Enum
import os

import gdown
from google.cloud import storage


class StorageEnum(Enum):
    GOOGLE_DRIVE = "gdrive"
    GCP = "gcp"


LOCAL_MODEL_PATH = "/tmp/models"


class GDriveStorage:
    def download(self, url: str, local_name: str) -> str:
        os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)
        model_path = os.path.join(LOCAL_MODEL_PATH, local_name)
        if not os.path.exists(model_path):
            gdown.download(url=url, output=model_path)
        return model_path


class GCSStorage:
    def download(self, url: str, local_name: str) -> str:
        os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)
        model_path = os.path.join(LOCAL_MODEL_PATH, local_name)
        if os.path.exists(model_path):
            return model_path

        bucket_name, blob_name = self._parse_gcs_url(url)
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(model_path)
        return model_path

    @staticmethod
    def _parse_gcs_url(url: str) -> tuple[str, str]:
        if not url.startswith("gs://"):
            raise ValueError(f"GCS model path must start with gs://, got: {url}")

        path = url.removeprefix("gs://")
        bucket_name, _, blob_name = path.partition("/")
        if not bucket_name or not blob_name:
            raise ValueError(f"Invalid GCS model path: {url}")

        return bucket_name, blob_name
