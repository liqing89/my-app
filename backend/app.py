from flask import Flask, jsonify, request
from flask_cors import CORS

# sys.path.append(os.path.dirname(__file__))
from echoGen import airbone_echo_gen

app = Flask(__name__)
CORS(app)  # 解决跨域问题

@app.route('/api/echoGen', methods=['GET'])
def getEchoData():
    result = airbone_echo_gen()

    if result == 1:
        return jsonify({"message": "Echo Data saved!"})
    else:
        return jsonify({"message": "Echo Data not saved."})

@app.route('/api/submit', methods=['POST'])
def submit_data():
    data = request.get_json()
    print("Received data:", data)
    return jsonify({"status": "success", "received_data": data})

if __name__ == '__main__':
    app.run(debug=True, port=5000)