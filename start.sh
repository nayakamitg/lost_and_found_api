#!/bin/bash
git clone https://github.com/ageitgey/face_recognition_models.git
cd face_recognition_models
python setup.py install
cd ..
echo "Starting App..."
gunicorn app:app
