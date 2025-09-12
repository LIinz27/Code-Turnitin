# Demo Implementation Guide - Code Turnitin Thesis Presentation

## Overview
This document outlines the step-by-step implementation of a local demo system for thesis presentation using existing Lab-IF repository dataset. The demo will showcase plagiarism detection capabilities without relying on live GitHub API calls.

## Prerequisites
- Existing Code Turnitin application (auto-discovery features removed)
- Lab-IF dataset: `tests/repo_analysis_Lab-IF_20250910_141914.json` (2,222 repositories)
- Flask application structure already in place

## Implementation Phases

### Phase 1: Data Preparation
**Objective**: Extract and prepare demo dataset from existing JSON file
**Files to modify**:
- Create: `data/demo/demo_repositories.json`
- Create: `src/utils/demo_data_extractor.py`

**Tasks**:
1. Parse the existing Lab-IF dataset JSON file
2. Filter repositories by primary languages (Java, JavaScript, Python)
3. Select 20 repositories from each language (60 total)
4. Create structured demo dataset with metadata
5. Ensure selected repositories have sufficient code content for similarity analysis

**Expected Output**: Clean demo dataset with 60 repositories ready for local testing

### Phase 2: Demo Backend Implementation
**Objective**: Create backend functionality for demo mode
**Files to modify**:
- Create: `src/demo/demo_handler.py`
- Modify: `src/app/web_routes.py` (add demo routes)
- Create: `src/demo/demo_similarity.py`

**Tasks**:
1. Implement demo repository loader
2. Create demo-specific similarity analysis functions
3. Add route handlers for demo functionality
4. Implement local file-based comparison logic
5. Mock GitHub API responses for demo mode

**Expected Output**: Functional backend supporting local demo operations

### Phase 3: Demo Frontend Implementation
**Objective**: Create user interface for demo presentation
**Files to modify**:
- Create: `templates/demo.html`
- Create: `static/js/demo.js`
- Create: `static/css/demo.css`
- Modify: `templates/index.html` (add demo navigation)

**Tasks**:
1. Design clean demo interface for thesis presentation
2. Implement repository selection dropdown
3. Create similarity analysis display components
4. Add live coding demonstration features
5. Implement result visualization for presentation

**Expected Output**: Professional demo interface suitable for thesis defense

### Phase 4: Testing & Documentation
**Objective**: Validate demo functionality and prepare presentation materials
**Files to modify**:
- Create: `tests/test_demo.py`
- Update: `docs/README.MD`
- Create: `DEMO_USAGE.md`

**Tasks**:
1. Test all demo functionality thoroughly
2. Validate similarity analysis accuracy
3. Document demo usage instructions
4. Prepare test cases for live coding demonstration
5. Create backup scenarios for presentation

**Expected Output**: Fully tested demo system with comprehensive documentation

## Dataset Information
- **Source**: Lab-IF organization repository analysis
- **Total Repositories**: 2,222
- **Primary Languages Distribution**:
  - Java: 915 repositories (41.2%)
  - JavaScript: 354 repositories (15.9%)
  - Python: 295 repositories (13.3%)
- **Selection Criteria**: Active repositories with substantial code content

## Demo Features
1. **Local Repository Selection**: Browse curated dataset without API calls
2. **Similarity Analysis**: Compare selected repositories using existing algorithms
3. **Live Coding Demonstration**: Show real-time analysis process
4. **Result Visualization**: Professional presentation of similarity scores
5. **Thesis-Friendly Interface**: Clean, academic-appropriate design

## Technical Architecture
```
demo/
├── demo_handler.py          # Main demo logic
├── demo_similarity.py       # Local similarity analysis
└── __init__.py

data/demo/
└── demo_repositories.json   # Curated demo dataset

templates/
└── demo.html               # Demo interface

static/
├── js/demo.js             # Demo frontend logic
└── css/demo.css           # Demo-specific styles
```

## Implementation Timeline
- **Phase 1**: Data Preparation (30 minutes)
- **Phase 2**: Backend Implementation (45 minutes)
- **Phase 3**: Frontend Implementation (60 minutes)
- **Phase 4**: Testing & Documentation (30 minutes)

**Total Estimated Time**: 2.5 hours

## Success Criteria
- ✅ Demo runs completely offline (no GitHub API dependency)
- ✅ Professional presentation interface
- ✅ Accurate similarity analysis results
- ✅ Smooth live coding demonstration capability
- ✅ Comprehensive test coverage

## Next Steps
Start with Phase 1: Data Preparation by executing the data extraction process from the existing Lab-IF dataset.

---
*This implementation guide supports thesis presentation requirements for Code Turnitin plagiarism detection system.*
