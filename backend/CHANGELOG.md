# Changelog

## [Unreleased]

### Added

- Added more robust biomarker validation to filter out non-biomarker content
- Added test script for manual validation of biomarker data
- Added integration test for biomarker validation logic

### Changed

- Enhanced Claude prompt to be more specific about valid biomarkers
- Improved text preprocessing to better handle method descriptions
- Updated biomarker validation to filter out:
  - Numeric-only names (e.g., "100", "150")
  - Ordinal numbers (e.g., "2nd", "3rd")
  - Time descriptions (e.g., "4 am", "between Evening 6-10 pm")
  - Method descriptions (e.g., ") LDH, UV kinetic")
- Fixed parenthesis handling for biomarker names with descriptive suffixes
- Enhanced validation in both the extraction process and storage process

### Fixed

- Fixed duplicate biomarker storage when the same file is uploaded multiple times
- Fixed extraction of test method descriptions as separate biomarkers
- Fixed handling of reference ranges in biomarker data
- Added more comprehensive validation before storing biomarkers

## [1.0.0] - 2025-03-01

### Added

- Initial release 