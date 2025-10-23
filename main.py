Import re
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS # Required for cross-origin requests from the frontend

# --- Conversion Helpers (Core Logic) ---

def tiny_minify(html: str) -> str:
    """Removes comments, excess whitespace, and leading/trailing whitespace."""
    html = re.sub(r'<!--(?!\[if)([\s\S]*?)-->', '', html)
    html = re.sub(r'[ \t]{2,}', ' ', html)
    html = re.sub(r'^[ \t]+|[ \t]+$', '', html, flags=re.M)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

def escape_for_template_literal(s: str) -> str:
    """Escapes characters for use inside a JavaScript template literal."""
    s = s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    return s

def build_payload(escaped_html: str) -> str:
    """Wraps the escaped HTML in the document.write JavaScript payload."""
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
    """Base64 encodes the payload and wraps it in eval(atob())."""
    b64 = base64.b64encode(payload.encode('utf-8')).decode('ascii')
    return f"eval(atob('{b64}'));"

def convert_html_to_jso_string(html_input: str) -> str:
    """Main public function to perform the full conversion sequence."""
    if not html_input:
        return ""
    minified_html = tiny_minify(html_input)
    escaped_html = escape_for_template_literal(minified_html)
    js_payload = build_payload(escaped_html)
    return obfuscate_to_eval_atob(js_payload)

# --- Flask Server Setup ---

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

@app.route('/api/obfuscate', methods=['POST'])
def obfuscate_endpoint():
    """Endpoint that receives HTML and returns the obfuscated JSO."""
    try:
        data = request.json
        html_input = data.get('html', '')
        
        if not html_input or not isinstance(html_input, str):
            return jsonify({'error': 'Invalid or missing HTML input.'}), 400

        jso_result = convert_html_to_jso_string(html_input)
        return jsonify({'jso': jso_result})

    except Exception as e:
        # Log the error for debugging on the server
        print(f"Server error during obfuscation: {e}")
        return jsonify({'error': f'An unexpected server error occurred: {str(e)}'}), 500

@app.route('/')
def index():
    """Simple health check endpoint."""
    return "JSO Converter API is running.", 200

if __name__ == '__main__':
    # When deploying to Render, the HOST and PORT should be set by the environment.
    # For local testing, use:
    app.run(host='127.0.0.1', port=5000, debug=True)
