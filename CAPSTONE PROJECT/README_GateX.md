# 🚗 GateX - Automated Parking Authentication System

GateX is an Automatic Number Plate Recognition (ANPR) based parking authentication system that automates vehicle entry verification using Computer Vision and OCR.

The system detects vehicle number plates from images, extracts registration numbers using OCR, validates them against Indian vehicle registration formats, and verifies authorization through a SQLite database. Based on the verification result, the system returns an **ALLOW** or **DENY** response.


## 🏗️ System Architecture

```text
Camera / Client Device
          │
          ▼
     Flask Server
          │
          ▼
   Image Processing
(OpenCV + Contour Detection)
          │
          ▼
      Plate ROI
          │
          ▼
      EasyOCR
          │
          ▼
   Text Validation
      (Regex)
          │
          ▼
   SQLite Database
          │
          ▼
    ALLOW / DENY
```

### Software
- Python
- Flask
- OpenCV
- EasyOCR
- SQLite
- NumPy
- Regular Expressions (Regex)

### Hardware
- Raspberry Pi
- USB Webcam / Camera Module
- LED Indicator
- Gate Control Mechanism (Future Integration)

## 🔄 Working Flow

1. Vehicle image is captured.
2. Image is sent to the Flask server.
3. OpenCV performs:
   - Grayscale conversion
   - Noise reduction
   - Edge detection
   - Contour detection
4. Candidate number plate regions are extracted.
5. OCR is performed using EasyOCR.
6. Extracted text is validated using Indian plate format rules.
7. Plate number is checked against the SQLite database.
8. System returns:
   - ALLOW → Authorized vehicle
   - DENY → Unauthorized vehicle

### Response Example

```json
{
  "status": "ALLOW",
  "plate": "MH12AB1234"
}
```
 This project was made in collaboration with my classmates. My contribution was handling computer vision logic using openCV, easyOCR. Most of the work done on the laptop server was programmed by me.