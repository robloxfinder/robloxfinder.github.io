import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- THE FIX IS ON THIS LINE ---
# We are telling Flask to look for HTML files in the main directory ('.')
# instead of the default 'templates' folder.
app = Flask(__name__, template_folder='.')
# --- END OF FIX ---

# Enable CORS to allow your frontend to call this backend
CORS(app)

# --- API KEY CYCLING LOGIC ---

# 1. Load all keys from the .env file as a single string
api_keys_str = os.getenv("GEMINI_API_KEYS")

# 2. Split the string into a list of keys
all_keys = [key.strip() for key in (api_keys_str or "").split(',') if key.strip()]

# 3. Check if any keys were loaded
if not all_keys:
    print("FATAL ERROR: GEMINI_API_KEYS not found or empty in .env file.")

# 4. A global variable to track which key to use next.
current_key_index = 0

# --- FLASK ROUTES ---

# This route serves your main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# This is the endpoint your JavaScript will call
@app.route('/find_games', methods=['POST'])
def find_games():
    global current_key_index

    if not all_keys:
        return jsonify({"error": "API keys are not configured on the server. The admin needs to set them up."}), 500

    try:
        api_key_to_use = all_keys[current_key_index]
        genai.configure(api_key=api_key_to_use)
        
        print(f"--- Using API Key index: {current_key_index} ---")

        current_key_index = (current_key_index + 1) % len(all_keys)

        filters = request.json
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        Find 3 Roblox games based on these criteria:
        - Description: {filters.get('description', 'any')}
        - Genres: {', '.join(filters.get('genres', []))}
        - Playing with a group: {'Yes' if filters.get('withGroup') else 'No'}
        - Device: {filters.get('device', 'Any')}
        - Mechanics: {', '.join(filters.get('mechanics', []))}
        - Vibes: {', '.join(filters.get('vibes', []))}

        Return ONLY a valid JSON array of objects with the following keys for each game:
        "gameName", "urlName", "gameId", "description", "matchRating".

        - urlName should be a URL-friendly version of the name.
        - matchRating must be a number from 1 to 10.
        - The description should be short, engaging, and about 2-3 sentences.
        - Do not include any text, markdown, or formatting outside of the JSON array.
        
        Example response:
        [
          {{
            "gameName": "Adopt Me!",
            "urlName": "Adopt-Me",
            "gameId": 920587237,
            "description": "A relaxing social game where you can adopt pets and build a home.",
            "matchRating": 9
          }}
        ]
        """

        response = model.generate_content(prompt)
        
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        game_suggestions = json.loads(cleaned_text)
        return jsonify(game_suggestions)

    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from Gemini response:", cleaned_text)
        return jsonify({"error": "The AI returned an invalid response. Please try again."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An server error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)