from flask import Flask, request, jsonify
import cv2
import numpy as np
import easyocr
import sqlite3
import re
import os
import socket

app = Flask(__name__)

reader = easyocr.Reader(['en'], gpu=False)

DB_PATH = r"B:\Final Year Project\vehicles.db"
SERVER_HOST = os.getenv("ANPR_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("ANPR_PORT", "5000"))

PLATE_RAT_MIN = 1.2
PLATE_RAT_MAX = 6.0


# ---------------- DATABASE CHECK ----------------
def check_plate_in_database(plate_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT is_allowed FROM Vehicles WHERE plate_number = ?",
        (plate_number,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return bool(result[0])
    return False


# ---------------- SMART FIX + EXTRACTION ----------------
def smart_fix_and_extract(text):
    text = text.upper()
    text = text.replace("IND", "")
    text = ''.join(filter(str.isalnum, text))

    if len(text) < 8:
        return None

    # Try patterns:
    pattern1 = r'^([A-Z]{2})([0-9]{2})([A-Z])([0-9]{4})$'
    pattern2 = r'^([A-Z]{2})([0-9]{2})([A-Z]{2})([0-9]{4})$'

    possible_variants = [text]

    # If middle letter misread as 2, try Z correction
    if len(text) >= 5:
        temp = list(text)
        if temp[4] == '2':
            temp[4] = 'Z'
            possible_variants.append(''.join(temp))

    for variant in possible_variants:
        if re.match(pattern1, variant) or re.match(pattern2, variant):
            return variant

    return None


# ---------------- OCR RESULT HANDLER ----------------
def process_ocr_results(results):
    texts = []

    for bbox, text, conf in results:
        if conf > 0.3:
            texts.append(text)

    if not texts:
        return None

    combined = " ".join(texts)
    print("Combined OCR:", combined)

    plate = smart_fix_and_extract(combined)

    if plate:
        print("Final Plate:", plate)
        return plate

    return None


# ---------------- IMAGE PROCESSING ----------------
def process_image(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    median = cv2.medianBlur(gray, 3)
    blur = cv2.GaussianBlur(median, (5, 5), 0)
    bil = cv2.bilateralFilter(blur, 7, 75, 75)
    edges = cv2.Canny(bil, 100, 200)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    img_area = frame.shape[0] * frame.shape[1]
    candidate_regions = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < img_area * 0.0003:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, peri * 0.02, True)

        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)

            if h == 0:
                continue

            ratio = float(w) / float(h)

            if PLATE_RAT_MIN <= ratio <= PLATE_RAT_MAX:
                candidate_regions.append((x, y, w, h))

    candidate_regions = sorted(
        candidate_regions,
        key=lambda b: b[2] * b[3],
        reverse=True
    )

    # -------- TRY ROI FIRST ----------
    for (x, y, w, h) in candidate_regions:
        roi = gray[y:y+h, x:x+w]

        _, thresh = cv2.threshold(
            roi,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        resized = cv2.resize(thresh, (400, int(h * (400 / w))))

        results = reader.readtext(resized)
        print("ROI OCR:", results)

        plate = process_ocr_results(results)
        if plate:
            return plate

    # -------- FALLBACK FULL FRAME ----------
    print("Contour detection failed. Trying full image OCR.")

    results = reader.readtext(frame)
    print("FULL OCR:", results)

    plate = process_ocr_results(results)
    if plate:
        return plate

    return None


# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return "ANPR Server Running"


@app.route('/process', methods=['POST'])
def process():
    try:
        if 'image' not in request.files:
            return jsonify({
                "status": "ERROR",
                "message": "No image received"
            })

        file = request.files['image']
        img_bytes = file.read()

        npimg = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({
                "status": "ERROR",
                "message": "Image decode failed"
            })

        plate = process_image(frame)

        if plate:
            allowed = check_plate_in_database(plate)

            return jsonify({
                "status": "ALLOW" if allowed else "DENY",
                "plate": plate
            })

        return jsonify({
            "status": "DENY",
            "plate": None
        })

    except Exception as e:
        print("SERVER ERROR:", str(e))
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        })


if __name__ == "__main__":
    print("Using Database:", DB_PATH)
    try:
        lan_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        lan_ip = "unknown"
    print(f"Server starting on host={SERVER_HOST}, port={SERVER_PORT}")
    print(f"Local URL: http://127.0.0.1:{SERVER_PORT}/")
    print(f"LAN URL:   http://{lan_ip}:{SERVER_PORT}/")
    app.run(host=SERVER_HOST, port=SERVER_PORT, threaded=True)
