from enum import Enum
import os

import gdown


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
