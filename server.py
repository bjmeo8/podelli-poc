"""
Podelli POC - Web Server
Simple Flask server to visualize generated content
"""

from flask import Flask, render_template, send_from_directory, jsonify
import json
from pathlib import Path

app = Flask(__name__, template_folder='web_ui', static_folder='output')


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('web_ui', 'index.html')


@app.route('/api/metadata')
def get_metadata():
    """Get all assets metadata"""
    metadata_file = Path('output/assets_metadata.json')

    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({"assets": [], "generation_sessions": []})


@app.route('/api/universe')
def get_universe():
    """Get universe master data"""
    universe_file = Path('data/universe_master.json')

    if universe_file.exists():
        with open(universe_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({"error": "Universe file not found"}), 404


@app.route('/api/episodes')
def get_episodes():
    """Get all generated episode data"""
    episodes_dir = Path('output/episodes')
    episodes = []

    if episodes_dir.exists():
        for episode_file in episodes_dir.glob('*_complete.json'):
            with open(episode_file, 'r', encoding='utf-8') as f:
                episode_data = json.load(f)
                episodes.append(episode_data)

    return jsonify(episodes)


@app.route('/assets/<path:filepath>')
def serve_asset(filepath):
    """Serve generated assets (images, audio, video)"""
    return send_from_directory('output', filepath)


if __name__ == '__main__':
    print("\n< Starting Podelli POC Web Server...")
    print("=ñ Open your browser at: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
