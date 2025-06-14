# 🧠 Missing Persons Face Recognition API

This Flask-based API system allows registration of missing persons with their details and images, and supports face recognition to match unknown images with stored records.

---

## 📂 Project Structure

```
.
├── app.py                    # Main Flask application
├── known_people/             # Folder where known images are stored
├── missing_persons.db        # SQLite database file
├── requirements.txt          # Python dependencies
```

---

## 📀 Setup Instructions

### 1. 🔧 Install Dependencies

```bash
pip install flask face_recognition opencv-python numpy
```

If dlib is not installed (required for face recognition):

```bash
sudo apt install build-essential cmake
pip install dlib
```

### 2. ▶️ Run the App

```bash
python app.py
```

---

## 🧱 Database Structure

### `persons` Table

| Column             | Type                |
| ------------------ | ------------------- |
| id                 | INTEGER PRIMARY KEY |
| name               | TEXT                |
| mobile\_no         | TEXT                |
| address            | TEXT                |
| sex                | TEXT                |
| height             | TEXT                |
| guardian\_name     | TEXT                |
| year\_of\_birth    | INTEGER             |
| religion           | TEXT                |
| state              | TEXT                |
| district           | TEXT                |
| police\_station    | TEXT                |
| place\_of\_missing | TEXT                |
| missing\_from      | TEXT                |
| dd\_date           | TEXT                |
| reporting\_date    | TEXT                |
| report\_date       | TEXT                |
| other\_details     | TEXT                |
| tracing\_status    | TEXT                |

---

### `person_images` Table

| Column         | Type                         |
| -------------- | ---------------------------- |
| id             | INTEGER PRIMARY KEY          |
| person\_id     | INTEGER (FK to `persons.id`) |
| image\_path    | TEXT                         |
| face\_encoding | TEXT (stored as JSON)        |

---

## 📡 API Endpoints

---

### 1. `/add_person` — \[POST]

Registers a person and uploads their face image. Also stores face encoding.

**Request Type:** `multipart/form-data`

**Form Data:**

* All fields from `persons` table
* `image` (file)

**Response:**

```json
{
  "message": "Person and image saved successfully"
}
```

---

### 2. `/match_faces` — \[POST]

Accepts a face image and matches it with known persons from the database.

**Request Type:** `multipart/form-data`

**Form Data:**

* `image` (file)

**Response:**

```json
{
  "matches": [
    {
      "id": 1,
      "name": "Keli Devi",
      ...,
      "image": "known_people/keli_devi_123456.jpg",
      "confidence": 0.58
    }
  ]
}
```

---

### 3. `/get_person_by_id` — \[GET]

Fetches person data and images by ID.

**Query Param:** `?id=1`

**Response:**

```json
{
  "id": 1,
  "name": "Keli Devi",
  ...,
  "images": ["known_people/keli_devi_123456.jpg"]
}
```

---

### 4. `/get_person_by_name` — \[GET]

**Query Param:** `?name=Keli Devi`

**Response:**

```json
[
  {
    "id": 1,
    "name": "Keli Devi",
    ...,
    "images": ["known_people/keli_devi_123456.jpg"]
  }
]
```

---

### 5. `/all_registered` — \[GET]

Returns list of all registered persons with their image if available.

**Response:**

```json
[
  {
    "id": 1,
    "name": "Keli Devi",
    ...,
    "image": "known_people/keli_devi_123456.jpg"
  },
  ...
]
```

---

## 📊 Notes

* Face encodings are stored in the database as JSON.
* The `known_people/` folder holds saved face images.
* Confidence scores are derived using face distance from the recognition model.
* You can adjust `tolerance=0.6` in `compare_faces()` to tune accuracy.

---

## 📄 License

This project is for educational and humanitarian purposes.

```

---
Let me know if you want the same README in Hindi as well or if you'd like it saved as a downloadable file.

```
