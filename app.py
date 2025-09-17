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

        # --- START OF IMPROVED PROMPT ---
        # We are giving the AI a much stricter set of rules to prevent hallucinations.
        prompt = f"""
        You are an expert Roblox game recommender. Your primary goal is to provide REAL, POPULAR, and VERIFIABLE games from the Roblox platform. You must not invent games.

        A user is looking for games with these criteria:
        - Description: "{filters.get('description', 'any')}"
        - Genres: {', '.join(filters.get('genres', [])) or 'any'}
        - Playing with a group: {'Yes' if filters.get('withGroup') else 'No'}
        - Device: {filters.get('device', 'Any')}
        - Mechanics: {', '.join(filters.get('mechanics', [])) or 'any'}
        - Vibes: {', '.join(filters.get('vibes', [])) or 'any'}

        Your task is to find 3 real Roblox games that are a good match.

        **CRITICAL INSTRUCTIONS:**
        1.  **ACCURACY OVER CREATIVITY:** You must only return games that actually exist on Roblox.
        2.  **VALID `gameId` IS MANDATORY:** The `gameId` is the most important piece of information. It will be used to create a URL like `https://www.roblox.com/games/GAMEID/URLNAME`. An incorrect `gameId` makes the result useless. Ensure the `gameId` is the correct, official ID for the game on the Roblox website.
        3.  **PRIORITIZE POPULARITY:** Prefer well-known games that are likely to still be active.
        4.  **STRICT JSON OUTPUT:** Return ONLY a valid JSON array of objects. Do not include any introductory text, markdown, or anything outside of the `[...]`.

        The JSON object for each game must have these exact keys:
        - "gameName": The exact, official name of the game.
        - "urlName": A URL-friendly version of the name (e.g., "Adopt-Me").
        - "gameId": The correct, numeric ID of the game from its official Roblox page.
        - "description": A short, engaging description (2-3 sentences).
        - "matchRating": A number from 1 to 10 rating how well it matches the user's criteria.

        If you are not certain about a game's existence or its `gameId`, do not include it. It is better to return 1 or 2 accurate results than 3 invented ones.
        """
        # --- END OF IMPROVED PROMPT ---

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