# Audiobook-dl Test Plan

## Overview

This document outlines a comprehensive testing strategy for the audiobook-dl project. The current codebase has minimal test coverage (~1.2%, only 61 lines of tests) covering basic URL matching and output formatting. This test plan categorizes test cases by priority to guide systematic improvement of test coverage.

**Current State:**
- **Total Source Code:** ~5,276 lines
- **Test Code:** ~61 lines
- **Test Files:** 3 (test_urls.py, test_output.py, sources/test_storytel.py)
- **Coverage Gaps:** Authentication, downloads, encryption, metadata, FFmpeg operations, error handling, and 12 out of 13 source implementations

---

## Test Priority Definitions

- **CRITICAL:** Core functionality, data integrity, security, critical user workflows
- **HIGH:** Important features, error handling, common use cases
- **MEDIUM:** Edge cases, less common scenarios, validation
- **LOW:** Minor features, uncommon edge cases, cosmetic issues

---

## CRITICAL Priority Tests

### 1. Core Download Functionality

#### 1.1 Single Audiobook Download
- **Test:** Download a complete audiobook from each supported source
- **Verify:**
  - All audio files downloaded successfully
  - File integrity (checksums, playable files)
  - Download completes without crashes
- **File:** `audiobookdl/output/download.py:17-106`

#### 1.2 Series Download
- **Test:** Download a complete series with multiple books
- **Verify:**
  - All books in series identified
  - Each book downloaded separately
  - Proper series numbering/ordering
- **File:** `audiobookdl/__main__.py:147-160`

#### 1.3 Multi-threaded Download Safety
- **Test:** Concurrent file downloads with thread pool
- **Verify:**
  - No race conditions
  - All threads complete successfully
  - Progress tracking accurate
  - Thread cleanup on errors
- **File:** `audiobookdl/output/download.py:59-68`

### 2. Authentication & Authorization

#### 2.1 Cookie-based Authentication
- **Test:** Authenticate using cookies for each cookie-based source
- **Verify:**
  - Valid cookies accepted
  - Invalid cookies rejected with clear error
  - Expired cookies detected
  - Cookie persistence across requests
- **Sources:** audiobooks.com, Blinkist, Chirp, Everand, Overdrive, YourCloudLibrary
- **File:** `audiobookdl/sources/source/__init__.py:38-50`

#### 2.2 Username/Password Authentication
- **Test:** Login authentication for login-based sources
- **Verify:**
  - Valid credentials accepted
  - Invalid credentials rejected with clear error
  - Session management working
  - Password not logged or exposed
- **Sources:** BookBeat, eReolen, Nextory, Podimo, Saxo, Storytel
- **File:** `audiobookdl/__main__.py:135-140`

#### 2.3 Unauthorized Access Handling
- **Test:** Access without proper authentication
- **Verify:**
  - UserNotAuthorized exception raised
  - Clear error message to user
  - No partial downloads
- **File:** `audiobookdl/exceptions.py:7-9`

### 3. File Encryption & Decryption

#### 3.1 AES-128 Decryption
- **Test:** Download and decrypt AES-encrypted files
- **Verify:**
  - Decryption successful with valid key
  - Decrypted file is playable
  - File integrity maintained
- **File:** `audiobookdl/output/encryption.py:9-41`

#### 3.2 Encryption Key Retrieval
- **Test:** Extract encryption keys from various sources
- **Verify:**
  - Keys correctly parsed from M3U8 playlists
  - Key URLs resolved correctly
  - Invalid keys rejected
- **File:** `audiobookdl/output/encryption.py`

#### 3.3 Decryption Failure Handling
- **Test:** Handle missing or incorrect decryption keys
- **Verify:**
  - Clear error message
  - No corrupted output files
  - Cleanup of temporary files
- **File:** `audiobookdl/output/encryption.py`

### 4. Data Integrity

#### 4.1 Metadata Extraction Accuracy
- **Test:** Extract audiobook metadata from each source
- **Verify:**
  - Title, authors, narrators correct
  - ISBN, language, genres extracted
  - Publication date accurate
  - Description present and complete
- **File:** `audiobookdl/utils/audiobook.py:22-42`

#### 4.2 Cover Image Download
- **Test:** Download cover images
- **Verify:**
  - Image downloaded successfully
  - Valid image format (JPEG/PNG)
  - Image not corrupted
  - Proper resolution
- **File:** `audiobookdl/utils/image.py`

#### 4.3 Audio File Integrity
- **Test:** Verify downloaded audio files are valid
- **Verify:**
  - Files are playable
  - Duration matches expected
  - No corruption
  - Proper format (MP3, M4B, etc.)

---

## HIGH Priority Tests

### 5. FFmpeg Operations

#### 5.1 Audio File Combining
- **Test:** Combine multiple audio files into one
- **Verify:**
  - All files merged in correct order
  - No audio gaps or overlaps
  - Output file playable
  - Metadata preserved
- **File:** `audiobookdl/output/output.py:96-125`

#### 5.2 Format Conversion
- **Test:** Convert between audio formats (MP3 ↔ M4B)
- **Verify:**
  - Conversion successful
  - Audio quality maintained
  - Metadata transferred
  - File size reasonable
- **File:** `audiobookdl/output/output.py:128-159`

#### 5.3 FFmpeg Not Found
- **Test:** Run when FFmpeg is not installed
- **Verify:**
  - Clear error message
  - Helpful installation instructions
  - Graceful degradation where possible
- **File:** `audiobookdl/__main__.py:100-102`

#### 5.4 FFmpeg Progress Tracking
- **Test:** Monitor FFmpeg conversion progress
- **Verify:**
  - Progress percentage accurate
  - Progress bar updates smoothly
  - Completion detected correctly
- **File:** `audiobookdl/output/ffmpeg_progress.py`

### 6. Metadata Writing

#### 6.1 ID3 Tag Writing (MP3)
- **Test:** Write ID3v2 tags to MP3 files
- **Verify:**
  - Title, artist, album written
  - Cover art embedded
  - Chapter markers added
  - Tags readable by media players
- **File:** `audiobookdl/output/metadata/id3.py`

#### 6.2 MP4/M4B Tag Writing
- **Test:** Write metadata to M4B/M4A files
- **Verify:**
  - All metadata fields written
  - Cover art embedded
  - Chapter information included
  - Compatible with iTunes/Apple Books
- **File:** `audiobookdl/output/metadata/mp4.py`

#### 6.3 Chapter Information
- **Test:** Embed chapter markers
- **Verify:**
  - Chapter times accurate
  - Chapter titles correct
  - Seekable in media players
- **File:** `audiobookdl/output/metadata/ffmpeg.py:24-48`

#### 6.4 JSON Metadata Export
- **Test:** Export metadata to JSON file
- **Verify:**
  - Valid JSON format
  - All metadata included
  - File created alongside audiobook
- **File:** `audiobookdl/__main__.py:174-180`

### 7. Source Implementations

#### 7.1 URL Pattern Matching
- **Test:** Match URLs for all 13 sources
- **Verify:**
  - Valid URLs matched correctly
  - Invalid URLs rejected
  - Different URL formats handled
- **File:** `tests/test_urls.py` (exists, needs expansion)

#### 7.2 Page Parsing & Data Extraction
- **Test:** Extract data from source HTML/JSON
- **Verify:**
  - CSS selectors work
  - Regex patterns match
  - Missing data handled gracefully
- **File:** `audiobookdl/sources/source/__init__.py:102-174`

#### 7.3 Source-specific Tests per Platform
Each source needs tests for:
- URL matching
- Authentication flow
- Metadata extraction
- File URL retrieval
- Series detection
- Error handling

**Sources to test:**
1. audiobooks.com - `audiobookdl/sources/audiobooksdotcom.py`
2. Blinkist - `audiobookdl/sources/blinkist.py`
3. BookBeat - `audiobookdl/sources/bookbeat.py`
4. Chirp - `audiobookdl/sources/chirp.py`
5. eReolen - `audiobookdl/sources/ereolen.py`
6. Everand - `audiobookdl/sources/everand.py`
7. Librivox - `audiobookdl/sources/librivox.py`
8. Nextory - `audiobookdl/sources/nextory.py`
9. Overdrive - `audiobookdl/sources/overdrive.py`
10. Podimo - `audiobookdl/sources/podimo.py`
11. RSS - `audiobookdl/sources/rss.py`
12. Saxo - `audiobookdl/sources/saxo.py`
13. Storytel - `audiobookdl/sources/storytel.py` (partially tested)

### 8. Error Handling

#### 8.1 Network Errors
- **Test:** Handle connection failures, timeouts
- **Verify:**
  - Retry logic works
  - Clear error messages
  - Cleanup on failure
- **File:** `audiobookdl/sources/source/networking.py`

#### 8.2 Cloudflare Protection
- **Test:** Detect and handle Cloudflare blocking
- **Verify:**
  - CloudflareBlocked exception raised
  - Helpful error message
  - Custom SSL context applied
- **File:** `audiobookdl/exceptions.py:19-21`

#### 8.3 Book Not Available Errors
- **Test:** Handle BookNotReleased and BookHasNoAudiobook
- **Verify:**
  - Appropriate exception raised
  - Clear user message
  - No partial downloads
- **File:** `audiobookdl/exceptions.py:13-18`

#### 8.4 Data Not Present Errors
- **Test:** Handle missing elements on pages
- **Verify:**
  - DataNotPresent exception raised
  - Specific element identified in error
  - Graceful degradation
- **File:** `audiobookdl/exceptions.py:4-6`

### 9. Configuration Management

#### 9.1 Config File Loading
- **Test:** Load configuration from TOML files
- **Verify:**
  - Valid TOML parsed correctly
  - Invalid TOML rejected with clear error
  - Platform-specific paths work
- **File:** `audiobookdl/config.py:30-51`

#### 9.2 Config Priority
- **Test:** CLI args override config file
- **Verify:**
  - CLI arguments take precedence
  - Config file values used as defaults
  - Proper merging logic
- **File:** `audiobookdl/config.py:54-79`

#### 9.3 Default Config Values
- **Test:** Behavior with no config file
- **Verify:**
  - Sensible defaults applied
  - No crashes
  - Clear documentation of defaults

### 10. Output Path Handling

#### 10.1 Custom Output Templates
- **Test:** Generate paths with template variables
- **Verify:**
  - {author}, {title}, {narrator} substituted
  - {series}, {series_number} handled
  - {year}, {language} work correctly
- **File:** `audiobookdl/output/output.py:40-60`

#### 10.2 Path Sanitization
- **Test:** Remove invalid filename characters
- **Verify:**
  - Platform-specific invalid chars removed
  - Unicode characters handled
  - No path traversal vulnerabilities
- **File:** `audiobookdl/output/output.py:20-38`

#### 10.3 Character Removal Feature
- **Test:** --remove-chars functionality
- **Verify:**
  - Specified characters removed
  - Regex patterns work
  - None value handled correctly
- **File:** `audiobookdl/output/output.py:22-28`

---

## MEDIUM Priority Tests

### 11. CLI Argument Parsing

#### 11.1 Required Arguments
- **Test:** URL or --input-file required
- **Verify:**
  - Error if neither provided
  - Error if URL invalid
  - Both not allowed simultaneously

#### 11.2 Optional Arguments
- **Test:** All 25+ CLI options
- **Verify:**
  - Each flag works correctly
  - Short and long forms work
  - Help text accurate

#### 11.3 Batch Input File
- **Test:** --input-file with multiple URLs
- **Verify:**
  - All URLs processed
  - Errors in one don't stop others
  - Progress tracked correctly
- **File:** `audiobookdl/__main__.py:110-115`

### 12. M3U8 Playlist Handling

#### 12.1 Playlist Parsing
- **Test:** Parse M3U8 playlists
- **Verify:**
  - All segments extracted
  - Segment order preserved
  - Encryption info parsed

#### 12.2 Variant Streams
- **Test:** Handle M3U8 with multiple quality options
- **Verify:**
  - Highest quality selected
  - User can override selection

### 13. Image Processing

#### 13.1 Cover Image Normalization
- **Test:** Resize and normalize cover images
- **Verify:**
  - Images resized to standard dimensions
  - Aspect ratio preserved
  - Quality acceptable
- **File:** `audiobookdl/utils/image.py`

#### 13.2 Image Format Conversion
- **Test:** Convert between image formats
- **Verify:**
  - PNG ↔ JPEG conversion works
  - Transparency handled
  - File size optimized

### 14. Skip Downloaded Feature

#### 14.1 Already Downloaded Detection
- **Test:** --skip-downloaded flag
- **Verify:**
  - Existing files detected
  - Download skipped with message
  - Partial downloads re-attempted
- **File:** `audiobookdl/__main__.py:161-167`

### 15. Logging & Output

#### 15.1 Log Levels
- **Test:** --debug, --quiet flags
- **Verify:**
  - Debug shows detailed info
  - Quiet suppresses non-errors
  - Default shows progress

#### 15.2 Progress Bars
- **Test:** Rich library progress bars
- **Verify:**
  - Download progress accurate
  - Multiple concurrent downloads shown
  - Progress updates smooth

#### 15.3 Verbose FFmpeg Output
- **Test:** --verbose-ffmpeg flag
- **Verify:**
  - FFmpeg output shown
  - Useful for debugging
  - Not shown by default

### 16. Edge Cases - Metadata

#### 16.1 Missing Optional Metadata
- **Test:** Audiobook with minimal metadata
- **Verify:**
  - Required fields present
  - Optional fields gracefully missing
  - No crashes

#### 16.2 Special Characters in Metadata
- **Test:** Unicode, emojis, special chars
- **Verify:**
  - Characters preserved
  - File naming handles them
  - Tags written correctly

#### 16.3 Multiple Authors/Narrators
- **Test:** Books with multiple contributors
- **Verify:**
  - All names captured
  - Proper formatting (commas, &, etc.)
  - Metadata tags support lists

### 17. Series Handling

#### 17.1 Series Detection
- **Test:** Identify series vs single book
- **Verify:**
  - Series correctly identified
  - Single books not treated as series
  - Series metadata extracted

#### 17.2 Series Numbering
- **Test:** Books numbered correctly
- **Verify:**
  - Proper sequential numbering
  - Decimal numbers (e.g., 1.5) handled
  - Missing numbers detected

---

## LOW Priority Tests

### 18. Help & Documentation

#### 18.1 Help Text
- **Test:** --help flag
- **Verify:**
  - All options documented
  - Examples included
  - Version shown

#### 18.2 Version Display
- **Test:** --version flag
- **Verify:**
  - Correct version shown (0.7.7)
  - Format consistent

### 19. Platform Compatibility

#### 19.1 Cross-platform Paths
- **Test:** Path handling on Windows, macOS, Linux
- **Verify:**
  - Config dirs correct per platform
  - Path separators handled
  - No hardcoded paths

#### 19.2 Line Ending Handling
- **Test:** Input files with different line endings
- **Verify:**
  - CRLF and LF both work
  - No extra whitespace issues

### 20. Uncommon Scenarios

#### 20.1 Very Long Audiobooks
- **Test:** Audiobooks with 100+ files
- **Verify:**
  - All files downloaded
  - Memory usage reasonable
  - Progress tracking works

#### 20.2 Very Short Audiobooks
- **Test:** Single file audiobooks
- **Verify:**
  - No unnecessary processing
  - Combine step skipped
  - Fast completion

#### 20.3 Empty Series
- **Test:** Series with no available books
- **Verify:**
  - Clear error message
  - No crashes
  - Graceful exit

### 21. User Experience

#### 21.1 Error Message Quality
- **Test:** Review all error messages
- **Verify:**
  - Clear and actionable
  - No technical jargon
  - Include solutions

#### 21.2 Progress Information
- **Test:** User feedback during long operations
- **Verify:**
  - Never silent for >5 seconds
  - Clear what's happening
  - Time estimates when possible

---

## Testing Strategy Recommendations

### Phase 1: Critical Coverage (Immediate)
1. Set up testing framework with pytest
2. Add fixtures for mock audiobook data
3. Implement critical authentication tests
4. Add download integrity tests
5. Add encryption/decryption tests

**Target:** 50% code coverage of critical paths

### Phase 2: High Priority (Short-term)
1. Add FFmpeg operation tests (with mocking)
2. Complete metadata writing tests
3. Add tests for all 13 sources (at least basic)
4. Implement comprehensive error handling tests

**Target:** 70% code coverage

### Phase 3: Medium Priority (Medium-term)
1. Edge case testing
2. Integration tests for full workflows
3. CLI argument validation tests
4. Configuration management tests

**Target:** 85% code coverage

### Phase 4: Low Priority (Long-term)
1. Platform compatibility tests
2. Performance/stress tests
3. User experience validation
4. Documentation verification

**Target:** 90%+ code coverage

---

## Testing Infrastructure Needs

### Required Tools
- **pytest:** Test framework
- **pytest-cov:** Coverage reporting
- **pytest-mock:** Mocking support
- **responses:** HTTP mocking for requests
- **pytest-asyncio:** If async tests needed

### Mock Requirements
- Mock HTTP responses for each source
- Mock FFmpeg commands and output
- Mock file system operations
- Mock authentication services

### Test Data
- Sample M3U8 playlists
- Sample audiobook metadata
- Sample audio files (small, for testing)
- Sample cover images
- Sample encryption keys

### CI/CD Integration
- Run tests on push/PR
- Coverage reports to codecov or similar
- Test matrix: Python 3.9, 3.10, 3.11, 3.12
- Platform matrix: Ubuntu, macOS, Windows

---

## Metrics & Goals

### Current State
- **Test Coverage:** ~1.2%
- **Test Files:** 3
- **Test Cases:** ~5
- **LOC Tested:** 61 lines

### Target State
- **Test Coverage:** 85%+ (critical paths 100%)
- **Test Files:** 50+
- **Test Cases:** 500+
- **LOC Tested:** 4,000+ lines

### Success Criteria
- Zero critical functionality untested
- All sources have basic test coverage
- All error conditions tested
- CI/CD passing on all platforms
- No regressions in new releases

---

## Appendix: File Coverage Map

### Fully Untested (0% coverage)
- `audiobookdl/__main__.py` - Main orchestration
- `audiobookdl/config.py` - Configuration loading
- `audiobookdl/output/download.py` - Download logic
- `audiobookdl/output/encryption.py` - Encryption handling
- `audiobookdl/output/metadata/*` - All metadata modules
- `audiobookdl/utils/image.py` - Image processing
- 12 of 13 source implementations

### Partially Tested (<50% coverage)
- `audiobookdl/output/output.py` - Some output tests exist
- `audiobookdl/sources/storytel.py` - Basic URL parsing tested

### Well Tested (>50% coverage)
- None currently

---

## Notes

- This test plan is living document and should be updated as the codebase evolves
- Priority may shift based on bug reports and user feedback
- Some tests may require actual accounts on supported services (consider test accounts)
- Mock data should be maintained separately from test code
- Test execution time should be monitored to keep suite fast

**Document Version:** 1.0
**Created:** 2025-11-05
**Last Updated:** 2025-11-05
