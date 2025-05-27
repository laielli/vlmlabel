# VLM Label Test Suite

This directory contains all test scripts for the VLM Label video annotation tool, organized by test type and functionality.

## 📁 Test Organization

### 🔧 [Unit Tests](./unit/)
Tests for individual components and functions in isolation.

- **[test_annotation_fixes.py](./unit/test_annotation_fixes.py)** - Unit tests for annotation system fixes and validation

### 🔗 [Integration Tests](./integration/)
Tests that verify multiple components working together.

- **[test_routes.py](./integration/test_routes.py)** - Flask route integration tests

### ⚙️ [Preprocessing Tests](./preprocessing/)
Tests for video preprocessing, frame extraction, and variant generation.

- **[test_preprocessing.py](./preprocessing/test_preprocessing.py)** - Core preprocessing pipeline tests
- **[test_iframe_processing.py](./preprocessing/test_iframe_processing.py)** - I-frame video processing tests
- **[test_consistent_frame_extraction.py](./preprocessing/test_consistent_frame_extraction.py)** - Frame extraction consistency tests
- **[test_fps_variants.py](./preprocessing/test_fps_variants.py)** - FPS variant generation tests

### 🎯 [Feature Tests](./features/)
Tests for specific application features and user-facing functionality.

- **[test_timestamp_extraction.py](./features/test_timestamp_extraction.py)** - Timestamp extraction system tests
- **[test_frame_alignment.py](./features/test_frame_alignment.py)** - Frame alignment accuracy tests
- **[test_frame_display_fix.py](./features/test_frame_display_fix.py)** - Frame display functionality tests

### 🛠️ [Test Utilities](.)
Helper scripts and utilities for testing.

- **[setup_test_videos.py](./setup_test_videos.py)** - Sets up test video files and directory structure

## 🚀 Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/ -v
```

### Run Tests by Category

#### Unit Tests
```bash
python -m pytest tests/unit/ -v
```

#### Integration Tests
```bash
python -m pytest tests/integration/ -v
```

#### Preprocessing Tests
```bash
python -m pytest tests/preprocessing/ -v
```

#### Feature Tests
```bash
python -m pytest tests/features/ -v
```

### Run Individual Test Files
```bash
# Example: Run timestamp extraction tests
python tests/features/test_timestamp_extraction.py

# Example: Run preprocessing tests
python tests/preprocessing/test_preprocessing.py
```

### Run Specific Test Functions
```bash
# Using pytest
python -m pytest tests/features/test_timestamp_extraction.py::test_extract_frame_timestamps -v
```

## 🔧 Test Setup

### Prerequisites
1. Install test dependencies:
   ```bash
   pip install pytest
   ```

2. Set up test videos (if needed):
   ```bash
   python tests/setup_test_videos.py
   ```

3. Ensure FFmpeg is installed and accessible

### Test Data
- Test videos are stored in `input_videos/` directory
- Test outputs are generated in `test_outputs/` directory
- Temporary test files are cleaned up automatically

## 📊 Test Coverage

### Preprocessing Pipeline
- ✅ Video variant generation
- ✅ Frame extraction accuracy
- ✅ I-frame processing
- ✅ FPS handling and validation
- ✅ Duration preservation

### Core Features
- ✅ Timestamp extraction precision
- ✅ Frame alignment accuracy
- ✅ Frame display functionality
- ✅ Annotation system validation

### Integration
- ✅ Flask route functionality
- ✅ API endpoint responses
- ✅ File serving and static content

## 🐛 Debugging Tests

### Verbose Output
```bash
python -m pytest tests/ -v -s
```

### Run with Debug Information
```bash
python -m pytest tests/ --tb=long
```

### Run Specific Test with Print Statements
```bash
python tests/features/test_timestamp_extraction.py
```

## 📝 Adding New Tests

### Test File Naming Convention
- Unit tests: `test_[component_name].py` in `unit/`
- Integration tests: `test_[integration_area].py` in `integration/`
- Preprocessing tests: `test_[preprocessing_feature].py` in `preprocessing/`
- Feature tests: `test_[feature_name].py` in `features/`

### Test Function Naming
- Use descriptive names: `test_extract_frame_timestamps_accuracy()`
- Group related tests in classes if needed
- Include setup and teardown methods for complex tests

### Test Categories Guidelines

#### Unit Tests (`unit/`)
- Test individual functions or classes
- Mock external dependencies
- Fast execution (< 1 second per test)
- No file I/O or network calls

#### Integration Tests (`integration/`)
- Test component interactions
- Include Flask app testing
- API endpoint validation
- Database interactions (if any)

#### Preprocessing Tests (`preprocessing/`)
- Video processing pipeline tests
- Frame extraction validation
- File generation and validation
- Performance benchmarks

#### Feature Tests (`features/`)
- End-to-end feature testing
- User workflow validation
- UI component testing
- Cross-browser compatibility (if applicable)

## 📈 Performance Testing

Some tests include performance benchmarks:

```bash
# Run preprocessing performance tests
python tests/preprocessing/test_preprocessing.py --benchmark

# Run timestamp extraction performance tests
python tests/features/test_timestamp_extraction.py --performance
```

## 🔄 Continuous Integration

Tests are designed to run in CI environments:

- All tests should be deterministic
- No external dependencies (except FFmpeg)
- Cleanup temporary files
- Provide clear error messages

## 📅 Last Updated

This test organization was created on May 27, 2025, consolidating all test scripts into a logical, maintainable structure. 