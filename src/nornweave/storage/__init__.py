"""Attachment storage backends.

NornWeave supports multiple storage backends:
- LocalFilesystemStorage: Store on local disk (development)
- S3Storage: Store in AWS S3 (production)
- GCSStorage: Store in Google Cloud Storage (production)
- DatabaseBlobStorage: Store as database BLOBs (simple deployment)
"""

from nornweave.storage.database import DatabaseBlobStorage
from nornweave.storage.gcs import GCSStorage
from nornweave.storage.local import LocalFilesystemStorage
from nornweave.storage.s3 import S3Storage

__all__ = [
    "DatabaseBlobStorage",
    "GCSStorage",
    "LocalFilesystemStorage",
    "S3Storage",
]
