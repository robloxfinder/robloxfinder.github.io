import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS to allow your frontend to call this backend
CORS(app)

# Configure the Gemini API key
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"Error: {e}")
    # You might want to handle this more gracefully
    # For now, the app will fail to start if the key is missing.


# This route serves your main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# This is the endpoint your JavaScript will call
@app.route('/find_games', methods=['POST'])
def find_games():
    if not genai.api_key:
        return jsonify({"error": "API key is not configured. The server admin needs to set it up."}), 500

    try:
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
        
        # Clean the response to ensure it's valid JSON
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
    # Use 0.0.0.0 to make it accessible on your local network
    app.run(host='0.0.0.0', port=5000, debug=True)