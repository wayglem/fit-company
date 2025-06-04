from flask import Flask, request, jsonify
import random
import time
from datetime import datetime

app = Flask(__name__)

exercises = [
    {"id": 101, "name": "Jumping Jacks", "sets": 3, "reps": "20-30", "muscle_groups": ["full_body"]},
    {"id": 102, "name": "Mountain Climbers", "sets": 4, "reps": "15-25", "muscle_groups": ["core", "legs"]},
    {"id": 103, "name": "Dips", "sets": 3, "reps": "8-12", "muscle_groups": ["triceps", "shoulders"]},
    {"id": 104, "name": "Deadlifts", "sets": 4, "reps": "6-10", "muscle_groups": ["back", "legs"]},
    {"id": 105, "name": "Sit-ups", "sets": 3, "reps": "15-20", "muscle_groups": ["core"]},
    {"id": 106, "name": "Wall Sit", "sets": 3, "duration": "45-90s", "muscle_groups": ["legs"]},
]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "service": "coach",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@app.route('/generate-wod', methods=['POST'])
def generate_wod():
    payload = request.get_json(force=True)

    time.sleep(random.uniform(1.5, 2.5))

    user_email = payload.get('user_email')
    excluded = payload.get('excluded_exercises', [])

    filtered = [ex for ex in exercises if ex["name"].lower() not in map(str.lower, excluded)]

    chosen = random.sample(filtered, min(5, len(filtered)))

    response = {
        "user_email": user_email,
        "exercises": chosen,
        "generated_at": time.time(),
        "source": "coach-service-v2"
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
