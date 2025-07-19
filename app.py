from flask import Flask, session, jsonify, request, Response
from flask_cors import CORS
from drive import drive_bp  # You can keep this if you want to retry Drive later
import os
import json
import csv

app = Flask(__name__)
app.secret_key = 'your_flask_secret_key_here'  # Use a real secret in production
CORS(app)
app.register_blueprint(drive_bp)

DATA_FILE = 'firearms.json'


# ----- Utility Functions -----
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# ----- API Routes -----
@app.route('/api/firearms', methods=['GET'])
def get_firearms():
    return jsonify(load_data())

@app.route('/api/firearms', methods=['POST'])
def add_firearm():
    data = load_data()
    new_item = request.get_json()
    data.append(new_item)
    save_data(data)
    return jsonify({"message": "Firearm added successfully"}), 201

@app.route('/api/firearms/<serial_number>', methods=['DELETE'])
def delete_firearm(serial_number):
    data = load_data()
    new_data = [item for item in data if item['serial_number'] != serial_number]
    if len(new_data) == len(data):
        return jsonify({"error": "Firearm not found"}), 404
    save_data(new_data)
    return jsonify({"message": "Firearm deleted successfully"}), 200

@app.route('/api/firearms/<serial_number>', methods=['PUT'])
def update_firearm(serial_number):
    data = load_data()
    updated = request.get_json()
    for i, item in enumerate(data):
        if item['serial_number'] == serial_number:
            data[i] = updated
            save_data(data)
            return jsonify({"message": "Firearm updated successfully"}), 200
    return jsonify({"error": "Firearm not found"}), 404


# ----- CSV Export -----
@app.route('/download/csv', methods=['GET'])
def download_csv():
    data = load_data()
    output = []

    # CSV Header
    output.append(['Name', 'Serial Number', 'Purchase Price', 'Current Value', 'Purchase Date', 'Notes'])

    for firearm in data:
        output.append([
            firearm.get('name', ''),
            firearm.get('serial_number', ''),
            firearm.get('purchase_price', ''),
            firearm.get('current_value', ''),
            firearm.get('purchase_date', ''),
            firearm.get('notes', '')
        ])

    # Convert list of lists to CSV string
    csv_string = '\n'.join([','.join(map(str, row)) for row in output])

    return Response(
        csv_string,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=firearms.csv"}
    )


# ----- Run App -----
if __name__ == '__main__':
    app.run(debug=True)
