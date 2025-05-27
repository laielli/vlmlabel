# VLM Label Documentation

This directory contains comprehensive documentation for the VLM Label video annotation tool, organized into logical categories for easy navigation.

## 📁 Documentation Structure

### 🎯 [Features](./features/)
Documentation for major features and capabilities of the application.

- **[TIMESTAMP_EXTRACTION_README.md](./features/TIMESTAMP_EXTRACTION_README.md)** - Comprehensive guide to the precise frame timestamp extraction system that improved frame clicking accuracy from ~90% to ~99.9%
- **[LARGE_FRAME_SCROLLER_SUMMARY.md](./features/LARGE_FRAME_SCROLLER_SUMMARY.md)** - Detailed documentation of the large frame scroller with 3-frame display, optimized thumbnails, and navigation controls
- **[MINIMIZE_FUNCTIONALITY_SUMMARY.md](./features/MINIMIZE_FUNCTIONALITY_SUMMARY.md)** - Complete guide to the minimize/maximize system that provides up to 780px of vertical space savings

### 🔧 [Implementation](./implementation/)
Technical implementation details, fixes, and system improvements.

- **[FRAME_ALIGNMENT_FIX_SUMMARY.md](./implementation/FRAME_ALIGNMENT_FIX_SUMMARY.md)** - Technical details of the frame alignment solution using precise timestamp extraction
- **[FRAME_DISPLAY_FIX_SUMMARY.md](./implementation/FRAME_DISPLAY_FIX_SUMMARY.md)** - Implementation of frame display improvements and video player enhancements
- **[ANNOTATION_FIXES_SUMMARY.md](./implementation/ANNOTATION_FIXES_SUMMARY.md)** - Annotation system improvements and validation enhancements
- **[FPS_FIXES_SUMMARY.md](./implementation/FPS_FIXES_SUMMARY.md)** - Frame rate detection and handling improvements
- **[IFRAME_INTEGRATION_README.md](./implementation/IFRAME_INTEGRATION_README.md)** - I-frame video processing integration and preprocessing pipeline
- **[REFACTOR_SUMMARY.md](./implementation/REFACTOR_SUMMARY.md)** - Major code refactoring and architectural improvements
- **[IMPROVEMENTS_SUMMARY.md](./implementation/IMPROVEMENTS_SUMMARY.md)** - General system improvements and optimizations

### 🧪 [Testing](./testing/)
Testing documentation, procedures, and validation guides.

- **[FRAME_EXTRACTION_TEST_README.md](./testing/FRAME_EXTRACTION_TEST_README.md)** - Comprehensive testing procedures for frame extraction and validation

### 🎨 [Design](./design/)
Design documents, specifications, and architectural decisions.

- **[consistent_frame_extraction.md](./design/consistent_frame_extraction.md)** - Design specification for consistent frame extraction across video variants
- **[extracting_frame_timestamps.md](./design/extracting_frame_timestamps.md)** - Original design document for the timestamp extraction solution
- **[PHASE2.md](./design/PHASE2.md)** - Phase 2 development planning and feature specifications

## 🚀 Quick Start

1. **New to the project?** Start with the main [README.md](../README.md) in the root directory
2. **Looking for a specific feature?** Check the [Features](./features/) directory
3. **Need implementation details?** Browse the [Implementation](./implementation/) directory
4. **Want to understand the design?** Review the [Design](./design/) directory
5. **Setting up testing?** See the [Testing](./testing/) directory

## 📊 Key Achievements

- **Frame Accuracy**: Improved from ~90% to ~99.9% through precise timestamp extraction
- **Performance**: 50-85% reduction in loading times through optimized thumbnails
- **Space Efficiency**: Up to 780px of vertical space recovery through minimize functionality
- **User Experience**: Professional UI with smooth animations, responsive design, and flexible workflow options

## 🔗 Related Files

- **Main Application**: `../app.py` - Flask web application
- **Video Processing**: `../iframe_video_processor.py` - Core video processing engine
- **Frontend**: `../static/js/script.js` - JavaScript application logic
- **Styling**: `../static/css/style.css` - Application styling and UI components
- **Test Suite**: `../tests/README.md` - Comprehensive test organization and documentation

## 📝 Contributing

When adding new documentation:

1. Place feature documentation in `features/`
2. Place implementation details in `implementation/`
3. Place testing procedures in `testing/`
4. Place design specifications in `design/`
5. Update this README.md with links to new documents

## 📅 Last Updated

This documentation structure was organized on May 27, 2025, consolidating all design and summary documents into a logical, navigable structure. 