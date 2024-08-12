from flask import Flask, request, jsonify
from func_call_autocorrect import chat_with_gemini
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/new-street', methods=['POST'])
def new_street():
    data = request.get_json()
    if 'description' not in data:
        return jsonify({"error": "Missing 'description' field in the request"}), 400

    try:
        # send the request to the chatbot and get the response in json format - streetmix_json, text or error
        result = chat_with_gemini(data['description']) 
        print("result: ", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
