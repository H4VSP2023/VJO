import re
import base64
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

def _m_html(h_str: str) -> str:
    h_str = re.sub(r'<!--(?!\[if)([\s\S]*?)-->', '', h_str)
    h_str = re.sub(r'[ \t]{2,}', ' ', h_str)
    h_str = re.sub(r'^[ \t]+|[ \t]+$', '', h_str, flags=re.M)
    h_str = re.sub(r'\n{3,}', '\n\n', h_str)
    return h_str.strip()

def _e_str(s: str) -> str:
    s = s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    return s

def _b_js(e_h: str) -> str:
    return (
        "(function(){\n"
        "  function go(){\n"
        "    document.open(); document.write(`" + e_h + "`); document.close();\n"
        "  }\n"
        "  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go);\n"
        "  else go();\n"
        "})();"
    )

def _jso_out(p_js: str) -> str:
    b64 = base64.b64encode(p_js.encode('utf-8')).decode('ascii')
    return f"eval(atob('{b64}'));"

def _do_c(h_in: str) -> str:
    if not h_in: return ""
    m_h = _m_html(h_in)
    e_h = _e_str(m_h)
    p_js = _b_js(e_h)
    return _jso_out(p_js)

app = Flask(__name__)
CORS(app)

@app.route('/api/obfuscate', methods=['POST'])
def _obf_rt():
    try:
        data = request.json
        h_in = data.get('html', '')
        
        if not h_in or not isinstance(h_in, str):
            return jsonify({'error': 'Invalid or missing HTML input.'}), 400

        jso_result = _do_c(h_in)
        return jsonify({'jso': jso_result})

    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'error': 'Internal server error.'}), 500

@app.route('/')
def _idx_rt():
    return send_file(os.path.join(app.root_path, 'index.html'))
