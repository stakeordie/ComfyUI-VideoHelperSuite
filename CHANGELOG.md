# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-10

### Added
- S3 upload functionality for video outputs
  - Support for AWS S3 bucket configuration
  - Automatic file upload to S3 after video generation
  - S3 URL generation for uploaded files
  - Environment variable support for AWS credentials
  - Support for both standard and encoded AWS secret keys
- Preview functionality improvements
  - Fixed video preview display in UI
  - Restored correct preview data structure

### Changed
- Updated project configuration for fork
- Improved error handling for S3 uploads
- Reduced logging verbosity
- Added new dependencies: boto3, python-dotenv

### Security
- Secure handling of AWS credentials through environment variables
- Removed credential logging
- Support for encoded secret keys with slash replacement
