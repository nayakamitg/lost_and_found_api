
from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import os
import numpy as np
from PIL import Image
import time
import sqlite3
import json

app = Flask(__name__)
CORS(app)

known_faces = []
known_names = []
known_files = []  # Track filenames of saved face images
known_dir = "known_people"


def load_known_faces():
    known_faces.clear()
    known_names.clear()
    known_files.clear()
    for filename in os.listdir(known_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(known_dir, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_faces.append(encodings[0])
                # Remove file extension to get base name (can be full filename if you want)
                known_names.append(os.path.splitext(filename)[0])
                known_files.append(filename)
            else:
                print(f"[WARN] No face found in {filename}")

load_known_faces()
 
@app.route("/add_person", methods=["POST"])
def add_person():
    if 'image' not in request.files:
        return jsonify({"error": "Image is required"}), 400

    # Get image and fields
    file = request.files['image']
    data = request.form  # Use request.form to access text fields with multipart/form-data

    name = data.get("name").strip().lower()
    
    # Save face image to folder
    img = Image.open(file.stream)
    img_np = np.array(img)
    encodings = face_recognition.face_encodings(img_np)

    if not encodings:
        return jsonify({"error": "No face found"}), 400

    timestamp = int(time.time())
    filename = f"{name}_{timestamp}.jpg"
    image_path = os.path.join(known_dir, filename)
    img.save(image_path)

    # Insert into persons table
    conn = sqlite3.connect('missing_persons.db')
    cursor = conn.cursor()
    def get_or_none(field):
        value = data.get(field)
        return value if value and value.strip() != "" else None

    cursor.execute('''
    INSERT INTO persons (
        state, district, police_station, dd_date,
        place_of_missing, tracing_status, report_date, missing_from,
        reporting_date, year_of_birth, sex, religion, name,
        guardian_name, address, height, mobile_no, other_details
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    get_or_none("state"),
    get_or_none("district"),
    get_or_none("police_station"),
    get_or_none("dd_date"),
    get_or_none("place_of_missing"),
    get_or_none("tracing_status"),
    get_or_none("report_date"),
    get_or_none("missing_from"),
    get_or_none("reporting_date"),
    get_or_none("year_of_birth"),
    get_or_none("sex"),
    get_or_none("religion"),
    get_or_none("name"),
    get_or_none("guardian_name"),
    get_or_none("address"),
    get_or_none("height"),
    get_or_none("mobile_no"),
    get_or_none("other_details")
))

    person_id = cursor.lastrowid

    # Store image path + encoding
    encoding_list = encodings[0].tolist()
    cursor.execute('''
        INSERT INTO person_images (person_id, image_path, face_encoding)
        VALUES (?, ?, ?)
    ''', (
        person_id,
        image_path,
        json.dumps(encoding_list)
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": f"{name} registered with ID {person_id}",
        "image_path": image_path
    }), 200


@app.route("/match_faces", methods=["POST"])
def match_faces():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['image']
    try:
        img = np.array(Image.open(file.stream).convert("RGB"))
    except Exception as e:
        return jsonify({"error": f"Invalid image: {str(e)}"}), 400

    face_locations = face_recognition.face_locations(img)
    face_encodings = face_recognition.face_encodings(img, face_locations)

    if not face_encodings:
        return jsonify({"error": "No faces found in uploaded image"}), 400

    # Load known encodings from DB
    conn = sqlite3.connect("missing_persons.db")
    cursor = conn.cursor()
    cursor.execute("SELECT person_id, image_path, face_encoding FROM person_images")
    records = cursor.fetchall()
    conn.close()

    known_encodings = []
    known_ids = []
    known_files = []

    for person_id, image_path, encoding_json in records:
        try:
            encoding = np.array(json.loads(encoding_json))  # ✅ Corrected here
            known_encodings.append(encoding)
            known_ids.append(person_id)
            known_files.append(image_path)
        except Exception as e:
            continue  # skip malformed encodings

    matched = []

    for uploaded_encoding in face_encodings:
        distances = face_recognition.face_distance(known_encodings, uploaded_encoding)
        matches = face_recognition.compare_faces(known_encodings, uploaded_encoding, tolerance=0.6)

        for idx, is_match in enumerate(matches):
            if is_match:
                confidence = float(round(1 - distances[idx], 2))
                if confidence >= 0.5:
                    conn = sqlite3.connect("missing_persons.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM persons WHERE id= ?", (known_ids[idx],))
                    row = cursor.fetchone()
                    columns = [desc[0] for desc in cursor.description]
                    conn.close()

                    if row:
                        person_data = dict(zip(columns, row))
                        person_data["file"] = known_files[idx]
                        person_data["confidence"] = confidence
                        matched.append(person_data)


    if not matched:
        return jsonify({"matches": [], "message": "No known faces matched"}), 200

    return jsonify({"matches": matched}), 200



@app.route("/get_person_by_id", methods=["GET"])
def find_person_by_id():
    person_id = request.args.get("id")

    if not person_id:
        return jsonify({"error": "Missing 'id' in URL parameters"}), 400

    conn = sqlite3.connect('missing_persons.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
    row = cursor.fetchone()

    if row:
        columns = [desc[0] for desc in cursor.description]
        result = dict(zip(columns, row))
    else:
        result = {"status": "success", "message": "Not found"}

    conn.close()
    return jsonify(result), 200


@app.route("/get_person_by_name", methods=["GET"])
def find_person_by_name():
    name = request.args.get("name")
    
    if not name:
        return jsonify({"error": "Missing 'name' parameter in URL"}), 400

    conn = sqlite3.connect('missing_persons.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM persons WHERE name = ? OR name = ? OR name = ?;",
        (name.upper(), name.lower(), name.capitalize())
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()

    matched = [dict(zip(columns, row)) for row in rows]

    if matched:
        return jsonify(matched), 200
    else:
        return jsonify({"status": "success", "message": "Not found"}), 200

@app.route("/all_registered", methods=["GET"])
def get_all_persons():
    conn = sqlite3.connect('missing_persons.db')
    cursor = conn.cursor()

    # Step 1: Get all persons
    cursor.execute("SELECT * FROM persons")
    persons_rows = cursor.fetchall()
    persons_columns = [desc[0] for desc in cursor.description]

    all_persons = []

    for row in persons_rows:
        person_dict = dict(zip(persons_columns, row))
        person_id = person_dict['id']

        # Step 2: Check for image in person_images table
        cursor.execute("SELECT image_path FROM person_images WHERE person_id = ?", (person_id,))
        image_row = cursor.fetchone()

        if image_row:
            person_dict["image"] = image_row[0]
        else:
            person_dict["image"] = None  # Optional: or skip this key

        all_persons.append(person_dict)

    conn.close()
    return jsonify({"persons": all_persons}), 200



if __name__ == "__main__":
    app.run(debug=True, port=5000)