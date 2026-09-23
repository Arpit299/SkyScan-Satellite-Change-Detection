# SkyScan — Satellite Change Detection

SkyScan is a Python-based image analysis tool that compares before-and-after satellite imagery to detect, measure, and visualize geographic changes.

## Features

* Before/after image comparison
* Pixel-level change detection
* Configurable detection threshold
* Gaussian blur preprocessing
* Connected-component analysis
* Change-region detection
* Bounding-box generation
* Changed-area calculation
* Basic region classification
* Change-map generation
* Change-overlay visualization
* JSON report generation
* Automatic image-size normalization
* Built-in self-test

## Tech Stack

**Python | Pillow | Image Processing | Computer Vision | JSON | CLI**

## DSA Used

**deque | Set | Bytearray | Iterative Graph Traversal | Connected Components**

## Installation

```bash
pip install pillow
```

## Usage

Run the built-in self-test:

```bash
python skyscan.py --self-test
```

Compare two satellite images:

```bash
python skyscan.py before.png after.png
```

Set a custom detection threshold:

```bash
python skyscan.py before.png after.png --threshold 40
```

Set the minimum detected region size:

```bash
python skyscan.py before.png after.png --min-region 50
```

Generate a JSON report:

```bash
python skyscan.py before.png after.png --json skyscan_report.json
```

Specify an output directory:

```bash
python skyscan.py before.png after.png --output results
```

## Architecture

```text
Before Image
      +
After Image
      ↓
Image Normalization
      ↓
Noise Reduction
      ↓
Pixel Difference
      ↓
Thresholding
      ↓
Connected Components
      ↓
Region Analysis
      ↓
Change Classification
      ↓
Change Map + Overlay + JSON
```

## Example Output

```text
Image Size: 200x140
Changed Pixels: 4688
Changed Area: 16.7429%
Change Regions: 2
```

Each detected region includes:

```text
Region ID
Change Type
Pixel Count
Bounding Box
Affected Area
```

## Output Files

The analyzer generates:

```text
change_map.png
change_overlay.png
skyscan_report.json
```

The change map highlights detected regions, while the overlay draws bounding boxes over the original imagery.

## Purpose

Built to demonstrate image processing, connected-component algorithms, spatial analysis, threshold-based change detection, computer vision concepts, and Python-based geospatial analytics.

