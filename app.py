import re
import base64
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

def tiny_minify(html: str) -> str:
    html = re.sub(r'<!--(?!\[if)([\s\S]*?)-->', '', html)
    html = re.sub(r'[ \t]{2,}', ' ', html)
    html = re.sub(r'^[ \t]+|[ \t]+$', '', html, flags=re.M)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

def escape_for_template_literal(s: str) -> str:
    s = s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    return s

def build_payload(escaped_html: str) -> str:
    return (
        "(function(){\n"
        "  function go(){\n"
        "    document.open(); document.write(`" + escaped_html + "`); document.close();\n"
        "  }\n"
        "  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go);\n"
        "  else go();\n"
        "})();"
    )

def obfuscate_to_eval_atob(payload: str) -> str:
    b64 = base64.b64encode(payload.encode('utf-8')).decode('ascii')
    return f"eval(atob('{b64}'));"

def convert_html_to_jso_string(html_input: str) -> str:
    if not html_input:
        return ""
    minified_html = tiny_minify(html_input)
    escaped_html = escape_for_template_literal(minified_html)
    js_payload = build_payload(escaped_html)
    return obfuscate_to_eval_atob(js_payload)

app = Flask(__name__)
CORS(app)

@app.route('/api/obfuscate', methods=['POST'])
def obfuscate_endpoint():
    try:
        data = request.json
        html_input = data.get('html', '')
        
        if not html_input or not isinstance(html_input, str):
            return jsonify({'error': 'Invalid or missing HTML input.'}), 400

        jso_result = convert_html_to_jso_string(html_input)
        return jsonify({'jso': jso_result})

    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'error': 'Internal server error.'}), 500

@app.route('/')
def index():
    return send_file(os.path.join(app.root_path, 'index.html'))
