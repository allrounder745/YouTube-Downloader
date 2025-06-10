from flask import Flask, request, jsonify, send_file
from pytube import YouTube, Search
import os
import uuid

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"

# Ensure downloads directory exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "YouTube Downloader API is running"})


@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    query = data.get("query")
    mode = data.get("mode", "video")  # 'video' or 'audio'

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # If URL provided
    if query.startswith("http"):
        yt = YouTube(query)
    else:
        # Search YouTube for the first relevant result
        s = Search(query)
        if not s.results:
            return jsonify({"error": "No video found for this search term"}), 404
        yt = s.results[0]

    filename = str(uuid.uuid4()) + (".mp4" if mode == "video" else ".mp3")
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        if mode == "audio":
            stream = yt.streams.filter(only_audio=True).first()
            stream.download(output_path=DOWNLOAD_FOLDER, filename=filename)
        else:
            stream = yt.streams.get_highest_resolution()
            stream.download(output_path=DOWNLOAD_FOLDER, filename=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Generate temporary download link
    return jsonify({
        "title": yt.title,
        "download_url": request.host_url + "file/" + filename
    })


@app.route("/file/<filename>", methods=["GET"])
def serve_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
