# Minimal API stub used for smoke tests
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/api/clients')
def clients():
    return jsonify([{'id': 'c1', 'name': 'Test Client', 'phone': '000', 'created_at': '2025-01-01T00:00:00'}])


@app.route('/api/bookings', methods=['GET', 'POST'])
def bookings():
    if request.method == 'GET':
        return jsonify([])
    data = request.json or {}
    return jsonify({'id': 'b1', **data}), 201


@app.route('/api/services')
def services():
    return jsonify([])


@app.route('/api/masters')
def masters():
    return jsonify([])


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
