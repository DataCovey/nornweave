## ADDED Requirements

### Requirement: S3 extra provides AWS S3 storage support

The `[s3]` extra SHALL provide all dependencies needed for S3 attachment storage.

#### Scenario: Install s3 extra
- **WHEN** user runs `pip install nornweave[s3]`
- **THEN** `boto3` is installed

#### Scenario: S3 storage works after s3 extra install
- **WHEN** user has `[s3]` extra installed
- **AND** sets `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=s3`
- **AND** configures S3 bucket and credentials
- **THEN** attachments are stored in S3 successfully

#### Scenario: Clear error when S3 requested without extra
- **WHEN** user sets `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=s3` without `[s3]` extra
- **AND** attempts to store an attachment
- **THEN** a clear ImportError is raised
- **AND** error message includes: "boto3 is required for S3 storage. Install with: pip install boto3"

### Requirement: GCS extra provides Google Cloud Storage support

The `[gcs]` extra SHALL provide all dependencies needed for GCS attachment storage.

#### Scenario: Install gcs extra
- **WHEN** user runs `pip install nornweave[gcs]`
- **THEN** `google-cloud-storage` is installed

#### Scenario: GCS storage works after gcs extra install
- **WHEN** user has `[gcs]` extra installed
- **AND** sets `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=gcs`
- **AND** configures GCS bucket and credentials
- **THEN** attachments are stored in GCS successfully

#### Scenario: Clear error when GCS requested without extra
- **WHEN** user sets `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=gcs` without `[gcs]` extra
- **AND** attempts to store an attachment
- **THEN** a clear ImportError is raised
- **AND** error message includes: "google-cloud-storage is required for GCS storage"

## MODIFIED Requirements

### Requirement: All extra installs complete feature set

The `[all]` extra SHALL install all optional dependencies for full functionality.

#### Scenario: Install all extra
- **WHEN** user runs `pip install nornweave[all]`
- **THEN** all extras are installed: postgres, mcp, attachments, search, ratelimit, s3, gcs
