from flask import Flask, render_template, send_from_directory
import os
import logging

app = Flask(__name__, template_folder='templates', static_folder='static')

# 配置日志
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
@app.route('/home')
def home():
    app.logger.debug("Rendering home.html")
    return render_template('home.html')

@app.route('/cyber_flower')
def cyber_flower():
    file_path = os.path.join('cyber_flower', 'index.html')
    app.logger.debug(f"Serving {file_path}")
    if not os.path.exists(file_path):
        app.logger.error(f"File not found: {file_path}")
        return "Index file not found", 404
    return send_from_directory('cyber_flower', 'index.html')

@app.route('/cyber_flower/<path:filename>')
def cyber_flower_static(filename):
    file_path = os.path.join('cyber_flower', filename)
    app.logger.debug(f"Serving {file_path}")
    if not os.path.exists(file_path):
        app.logger.error(f"File not found: {file_path}")
        return "File not found", 404
    return send_from_directory('cyber_flower', filename)

if __name__ == '__main__':
    app.run(debug=True)