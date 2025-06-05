
from flask import Flask, request, jsonify, send_from_directory
from tryangel_v4_fusion_gtts_feedback import EnhancedTryAngel
import os

app = Flask(__name__)
instances = {}

def get_instance(user_id):
    if user_id not in instances:
        instances[user_id] = EnhancedTryAngel(user_id=user_id)
    return instances[user_id]

@app.route("/speak", methods=["POST"])
def speak():
    data = request.json
    user_id = data.get("user_id", "utilisateur_defaut_001")
    message = data.get("message")
    if not message:
        return jsonify({"error": "Message is required."}), 400
    instance = get_instance(user_id)
    response = instance.learner.generate_response(message)
    instance.save_memory(message, response)
    voice_path = instance._text_to_speech(response)
    voice_filename = os.path.basename(voice_path)
    print(f"✅ Fichier vocal généré : {voice_filename}")
    return jsonify({
        "user_id": user_id,
        "message": message,
        "response": response,
        "voice_path": f"/voices/{voice_filename}",
        "voice_url": f"http://127.0.0.1:5000/voices/{voice_filename}"
    })

@app.route("/voices/<filename>")
def serve_voice(filename):
    return send_from_directory("voices", filename)

@app.route("/memory", methods=["GET"])
def memory():
    user_id = request.args.get("user_id", "utilisateur_defaut_001")
    instance = get_instance(user_id)
    return jsonify(instance.memory)

if __name__ == "__main__":
    app.run(debug=True)
