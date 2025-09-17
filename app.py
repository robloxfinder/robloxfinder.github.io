import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='.')
CORS(app)

api_keys_str = os.getenv("GEMINI_API_KEYS")
all_keys = [key.strip() for key in (api_keys_str or "").split(',') if key.strip()]
if not all_keys:
    print("FATAL ERROR: GEMINI_API_KEYS not found or empty in .env file.")
current_key_index = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/find_games', methods=['POST'])
def find_games():
    global current_key_index
    if not all_keys:
        return jsonify({"error": "API keys are not configured on the server."}), 500

    try:
        api_key_to_use = all_keys[current_key_index]
        genai.configure(api_key=api_key_to_use)
        
        print(f"--- Using API Key index: {current_key_index} ---")
        current_key_index = (current_key_index + 1) % len(all_keys)

        filters = request.json
        model = genai.GenerativeModel('gemini-1.5-flash')

        # --- START OF THE ULTIMATE PROMPT ---
        # This prompt uses the "few-shot" technique by providing a list of real examples.
        # This dramatically reduces the chance of the AI inventing fake games.
        prompt = f"""
        You are a helpful and accurate Roblox game recommender. Your most important duty is to provide recommendations for REAL, VERIFIABLE Roblox games with correct game IDs.

        **Here is a reference list of real, popular Roblox games. Use this as your primary source of truth:**
        [
          {{ "gameName": "Adopt Me!", "urlName": "Adopt-Me", "gameId": 920587237, "genres": ["Roleplay", "Social"] }},
          {{ "gameName": "Blox Fruits", "urlName": "Blox-Fruits", "gameId": 2753915549, "genres": ["RPG", "Fighting", "Adventure"] }},
          {{ "gameName": "Tower of Hell", "urlName": "Tower-of-Hell", "gameId": 192800, "genres": ["Obby", "Platformer", "Competitive"] }},
          {{ "gameName": "Brookhaven RP", "urlName": "Brookhaven-RP", "gameId": 4924922222, "genres": ["Roleplay", "Social", "Town and City"] }},
          {{ "gameName": "Murder Mystery 2", "urlName": "Murder-Mystery-2", "gameId": 142823291, "genres": ["Horror", "Social", "Puzzle"] }},
          {{ "gameName": "Arsenal", "urlName": "Arsenal", "gameId": 286090429, "genres": ["Fighting", "FPS"] }},
          {{ "gameName": "Royale High", "urlName": "Royale-High", "gameId": 735030782, "genres": ["Roleplay", "Adventure", "Fashion"] }},
          {{ "gameName": "Natural Disaster Survival", "urlName": "Natural-Disaster-Survival", "gameId": 189707, "genres": ["Survival"] }},
          {{ "gameName": "Work at a Pizza Place", "urlName": "Work-at-a-Pizza-Place", "gameId": 192800, "genres": ["Roleplay", "Simulator", "Social"] }}
        ]

        A user is looking for a game with the following preferences:
        - Description: "{filters.get('description', 'any')}"
        - Selected Genres: {', '.join(filters.get('genres', [])) or 'any'}
        - Playing with a group: {'Yes' if filters.get('withGroup') else 'No'}

        **Your Task:**
        1.  Analyze the user's preferences.
        2.  Select the 3 best-matching games. **You should STRONGLY prefer games from the reference list above.**
        3.  If a game from the reference list is a good match, use its exact data.
        4.  If you absolutely must choose a game not on the list, you must be 100% certain it is a real, popular game and that you know its correct `gameId`. Do not guess.
        5.  Return ONLY a valid JSON array of objects. Do not write any other text or markdown.

        The JSON object for each game must have these keys: "gameName", "urlName", "gameId", "description", "matchRating".
        """
        # --- END OF THE ULTIMATE PROMPT ---

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