#!/usr/bin/env python3
"""
EVA Web Application - Exploit Vector Agent
A web-based interface for the EVA penetration testing AI assistant.
"""

import os
import sys
import json
import subprocess
import re
import time
import mimetypes
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    import requests
    from requests_toolbelt import MultipartEncoder
    import openai
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "requests-toolbelt", "openai"])
    import requests
    from requests_toolbelt import MultipartEncoder
    import openai

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
API_ENDPOINT = "NOT_SET"
openai.api_base = "https://g4f.dev/v1"
openai.api_key = "jl/JIooPPOcQoHgyW65Mhg13TbIB6CgxcRpJdxMfPRPHZD0oYwuFP29tW4PbkSSxr4U0mqe5kGb5RHVVWAVDgEIWhxujkxyDLRnC7j/PdUOY6UXX/WLrjd3RymPB3WQCGSH7G81iAFFXADpK9Arx8tBUPTNSCUBEw+H4/MyHiYAKlR12uEWHUE+6+8Qd6zEUoqa8VyZ0ZfGIS1BJU5MlXQ3C3vs3zTmP480uFMnvUlh/jCUJUuNlcXQu0ghVtgl1nJuFzMbQLqXUbWV8W9Fu13MChcL3udNczGcRzyteSnBiOOtzZuEU7prf/s/RmhAQ3bKMAFR+JMsmmvFMtyJcPqoXGezzr7GugZTtj6mexsmv84sUr4Js7K9UmJdtF9RmVbrY7UC45XwXcIUm0bpm660Nvn/rPASgSBG6LV5YbWKpq4J9djWApUYLNrY3qvUHs9/5bD0riXOpTYQTE2lOAZEraWcAgBgGeeyQwV/+lpwoihKUk8c9/lhwlMHzZ54e+0j7GHl24aLKlovQXHyUCaQNCTuR4yAzYPc5TTR/gROfE0JQpnZZMLqpIy108GDvLQ6iLxkvfA9zyFReKipUtFWAWMPE0fngAh3BvlZrN3f9DE1qIPmLIwAvBRjCVdHUoHfpp8Z8TbSMAov3G0V6hRYtuIVYieRaT3w6vKH0my0="
G4F_MODEL = "gpt-5-1-instant"
OLLAMA_MODEL = "jimscard/whiterabbit-neo:latest"
CONFIG_DIR = Path.home() / ".config" / "eva"
SESSIONS_DIR = CONFIG_DIR / "sessions"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
ENV_PATH = Path(".env")

# ================= UTILITY FUNCTIONS =================

def extract_json_anywhere(raw: str, depth=0):
    """Extract JSON from potentially messy LLM output."""
    if not raw or depth > 5:
        return None
    first = raw.find("{")
    if first == -1:
        return None
    raw = raw[first:].strip()
    try:
        outer = json.loads(raw)
    except Exception:
        return None
    if isinstance(outer, dict) and "analysis" in outer and "commands" in outer:
        return outer
    if isinstance(outer, dict) and "response" in outer:
        inner = outer["response"]
        if not isinstance(inner, str):
            return None
        inner = inner.strip()
        inner = re.sub(r"^```.*?\n", "", inner, flags=re.S)
        inner = re.sub(r"\n```$", "", inner, flags=re.S)
        return extract_json_anywhere(inner, depth + 1)
    return None


def normalize_response(resp):
    """Normalize LLM response to expected format."""
    if not isinstance(resp, dict):
        return {"analysis": "⚠️ Invalid LLM output.", "commands": []}
    return {
        "analysis": resp.get("analysis", "⚠️ Error with model response, please ask again."),
        "commands": resp.get("commands", [])
    }


def build_prompt(user_msg, last_output):
    """Build the EVA prompt for the LLM."""
    return f"""
You are EVA, an autonomous offensive security / red team AI built exclusively for authorized CTFs, labs, and penetration testing environments.

YOUR ROLE:
Think and act like an experienced red team operator.
Prioritize enumeration → attack surface expansion → vulnerability identification → exploitation → privilege escalation → lateral movement.
Assume the target is hostile and misconfigured unless proven otherwise.
Be proactive, aggressive, and methodical.

CRITICAL RULES (MANDATORY — FAILURE INVALIDATES RESPONSE):
Respond with VALID JSON ONLY.
Do NOT include markdown, comments, explanations outside JSON, or formatting symbols.
Do NOT include ``` or any wrapper text.
Output MUST parse with json.loads().

STRICT RESPONSE FORMAT (DO NOT DEVIATE):
{{
"analysis": "<detailed offensive reasoning, written as EVA's internal red-team thinking AND explanation to the operator>",
"commands": ["<shell command>", "<shell command>", "<shell command>"]
}}

ANALYSIS REQUIREMENTS:
The "analysis" field MUST:
Be multi-paragraph and detailed.
Explain WHY each finding matters offensively.
Correlate ports, services, versions, OS hints, and misconfigurations.
Hypothesize real attack paths (RCE, LFI, SMB abuse, AD misconfig, creds reuse, deserialization, weak services, etc.).
Reference likely CVEs, attack classes, or known weaknesses when applicable (by name or ID if known).
Clearly justify the next commands as part of a larger exploitation strategy.
Sound like a thinking red teamer, not a generic assistant.

COMMANDS REQUIREMENTS:
"commands" MUST:
ALWAYS contain at least ONE actionable command.
Be real Kali Linux shell commands.
Focus on enumeration, exploitation, or validation (never placeholders).
Avoid defensive tooling.
Prefer depth (targeted scans, scripts, exploit checks) over noisy actions.
Commands should logically follow from the analysis.
Assume tools common to Kali Linux are available.

CONTEXT:
Attacker OS: Kali Linux
Target OS: Windows
Engagement: Fully authorized CTF / Lab
Internet access is available for reconnaissance and vulnerability research.

LAST COMMAND OUTPUT:
{last_output if last_output else "NONE"}

USER INPUT:
{user_msg}

TASK:
Analyze the current situation offensively.
Decide the next best red team actions.
Drive the engagement forward toward exploitation.
If exploitation is not yet possible, aggressively expand reconnaissance until it is.

ABSOLUTE REMINDER:
OUTPUT JSON ONLY.
NO TEXT OUTSIDE JSON.
NO EXCUSES.
ALWAYS THINK LIKE AN ATTACKER.
"""


def get_openai_key():
    """Get OpenAI API key from environment or .env file."""
    key = os.getenv("OPENAI_API_KEY")
    if key and key.strip():
        return key.strip()
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key:
                    os.environ["OPENAI_API_KEY"] = key
                    return key
    return None


def set_openai_key(key):
    """Save OpenAI API key to .env file."""
    with open(ENV_PATH, "a") as f:
        f.write(f"\nOPENAI_API_KEY={key}\n")
    os.environ["OPENAI_API_KEY"] = key


# ================= LLM CLASS =================

class LLM:
    def __init__(self, backend):
        self.backend = backend
        self.history = []

    def query(self, user_msg, last_output=""):
        prompt = build_prompt(user_msg, last_output)
        self.history.append({"role": "user", "content": prompt})
        raw = ""

        if self.backend == "ollama":
            try:
                p = subprocess.run(
                    ["ollama", "run", OLLAMA_MODEL],
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=120
                )
                raw = p.stdout
            except Exception as e:
                raw = f'{{"analysis": "Error running Ollama: {str(e)}", "commands": []}}'

        elif self.backend == "g4f":
            try:
                r = openai.ChatCompletion.create(
                    model=G4F_MODEL,
                    messages=self.history
                )
                raw = r.get('choices', [{}])[0].get('message', {}).get('content', "")
            except Exception as e:
                raw = f'{{"analysis": "Error with G4F backend: {str(e)}", "commands": []}}'

        elif self.backend == "api":
            try:
                r = requests.post(
                    API_ENDPOINT,
                    json={"conversation": self.history},
                    timeout=120
                )
                raw = r.text
            except Exception as e:
                raw = f'{{"analysis": "Error with custom API: {str(e)}", "commands": []}}'

        elif self.backend == "gpt":
            try:
                client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
                completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=self.history
                )
                raw = completion.choices[0].message.content
            except Exception as e:
                raw = f'{{"analysis": "Error with OpenAI GPT: {str(e)}", "commands": []}}'

        elif self.backend == "demo":
            # Demo mode - returns simulated responses
            raw = json.dumps({
                "analysis": f"[DEMO MODE] Analyzing your request: '{user_msg}'\n\nIn a real scenario, EVA would analyze this input and provide detailed offensive security guidance. The AI would consider:\n\n1. Current reconnaissance data\n2. Potential attack vectors\n3. Known vulnerabilities for identified services\n4. Privilege escalation paths\n\nThis is a demonstration of the EVA interface. To use real AI backends, configure Ollama, OpenAI GPT, G4F, or a custom API endpoint.",
                "commands": ["echo 'Demo command 1 - nmap -sV target'", "echo 'Demo command 2 - gobuster dir -u http://target'", "echo 'Demo command 3 - nikto -h target'"]
            })

        data = extract_json_anywhere(raw)
        if not data:
            data = {
                "analysis": "⚠️ Error parsing model response. Please try again.",
                "commands": []
            }

        data = normalize_response(data)
        self.history.append({"role": "assistant", "content": raw})
        return data


# ================= EVA SESSION CLASS =================

class EvaSession:
    def __init__(self, session_path, backend):
        self.session_path = session_path
        self.last_output = ""
        self.backend = backend
        self.memory = {"backend": backend, "timeline": []}
        
        if session_path.exists():
            try:
                self.memory = json.loads(session_path.read_text())
                self.backend = self.memory.get("backend", backend)
            except:
                pass
        
        self.model = LLM(self.backend)

    def save(self):
        self.session_path.write_text(json.dumps(self.memory, indent=2))

    def query(self, user_msg):
        self.memory["timeline"].append({"type": "user", "content": user_msg})
        self.save()
        
        resp = self.model.query(user_msg, self.last_output)
        self.memory["timeline"].append({"type": "analysis", "content": resp["analysis"]})
        self.save()
        
        return resp

    def run_command(self, cmd):
        """Execute a shell command and return output."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout + result.stderr
            self.last_output = output
            self.memory["timeline"].append({
                "type": "command",
                "cmd": cmd,
                "output": output
            })
            self.save()
            return output
        except subprocess.TimeoutExpired:
            return "Command timed out after 60 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def analyze_output(self):
        """Ask EVA to analyze the last command output."""
        resp = self.model.query("Analyze the previous command output and continue.", self.last_output)
        self.memory["timeline"].append({"type": "analysis", "content": resp["analysis"]})
        self.save()
        return resp


# Global session storage
active_sessions = {}


# ================= FILE UPLOAD FUNCTIONS =================

def upload_to_imgbb(filepath, data, ext):
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    token = re.search(r'PF\.obj\.config\.auth_token="([^"]+)', s.get("https://imgbb.com").text).group(1)
    form = MultipartEncoder(fields={
        "source": ("image." + ext, data, mimetypes.guess_type("image." + ext)[0] or "image/jpeg"),
        "type": "file",
        "action": "upload",
        "timestamp": str(int(time.time() * 1000)),
        "auth_token": token
    })
    r = s.post("https://imgbb.com/json", data=form, headers={
        "Content-Type": form.content_type,
        "Origin": "https://imgbb.com",
        "Referer": "https://imgbb.com/upload",
        "Accept": "*/*"
    })
    r.raise_for_status()
    j = r.json()
    if "image" in j and "url" in j["image"]:
        return j["image"]["url"]
    raise Exception(str(j))


def upload_to_telegra(data, ext, mime):
    files = {'file': ('tmp.' + ext, data, mime)}
    r = requests.post("https://telegra.ph/upload", files=files)
    r.raise_for_status()
    img = r.json()
    if isinstance(img, list) and img:
        return 'https://telegra.ph' + img[0]['src']
    elif 'error' in img:
        raise Exception(img['error'])
    else:
        raise Exception("Upload failed: " + str(img))


def upload_to_catbox(data, ext, mime):
    files = {'fileToUpload': ('tmp.' + ext, data, mime)}
    data_payload = {'reqtype': 'upload'}
    r = requests.post("https://catbox.moe/user/api.php", data=data_payload, files=files)
    r.raise_for_status()
    url = r.text.strip()
    if url.startswith("http"):
        return url
    else:
        raise Exception("Upload failed: " + url)


def upload_file(filepath):
    """Upload a file to multiple providers with fallback."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)
    
    with open(filepath, "rb") as f:
        data = f.read()
    
    ext = filepath.split(".")[-1] or "jpg"
    mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
    
    providers = [
        ("imgbb.com", lambda: upload_to_imgbb(filepath, data, ext)),
        ("telegra.ph", lambda: upload_to_telegra(data, ext, mime)),
        ("catbox.moe", lambda: upload_to_catbox(data, ext, mime)),
    ]
    
    errors = []
    for provider_name, upload_func in providers:
        try:
            url = upload_func()
            return {"success": True, "url": url, "provider": provider_name}
        except Exception as e:
            errors.append(f"{provider_name}: {str(e)}")
            continue
    
    raise Exception("All upload providers failed: " + "; ".join(errors))


# ================= FLASK ROUTES =================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all available sessions."""
    sessions = list(SESSIONS_DIR.glob("*.json"))
    session_list = []
    for s in sessions:
        try:
            data = json.loads(s.read_text())
            session_list.append({
                "name": s.stem,
                "backend": data.get("backend", "unknown"),
                "messages": len(data.get("timeline", []))
            })
        except:
            session_list.append({"name": s.stem, "backend": "unknown", "messages": 0})
    return jsonify({"sessions": session_list})


@app.route('/api/sessions/create', methods=['POST'])
def create_session():
    """Create a new session."""
    data = request.json
    backend = data.get("backend", "demo")
    name = data.get("name", f"session{int(time.time())}")
    
    session_path = SESSIONS_DIR / f"{name}.json"
    if session_path.exists():
        return jsonify({"error": "Session already exists"}), 400
    
    session = EvaSession(session_path, backend)
    session.save()
    active_sessions[name] = session
    
    return jsonify({"success": True, "session": name, "backend": backend})


@app.route('/api/sessions/<name>/load', methods=['GET'])
def load_session(name):
    """Load an existing session."""
    session_path = SESSIONS_DIR / f"{name}.json"
    if not session_path.exists():
        return jsonify({"error": "Session not found"}), 404
    
    try:
        data = json.loads(session_path.read_text())
        backend = data.get("backend", "demo")
        session = EvaSession(session_path, backend)
        active_sessions[name] = session
        
        return jsonify({
            "success": True,
            "session": name,
            "backend": backend,
            "timeline": data.get("timeline", [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sessions/<name>/delete', methods=['DELETE'])
def delete_session(name):
    """Delete a session."""
    session_path = SESSIONS_DIR / f"{name}.json"
    if session_path.exists():
        session_path.unlink()
        if name in active_sessions:
            del active_sessions[name]
        return jsonify({"success": True})
    return jsonify({"error": "Session not found"}), 404


@app.route('/api/chat', methods=['POST'])
def chat():
    """Send a message to EVA and get a response."""
    data = request.json
    session_name = data.get("session")
    message = data.get("message", "")
    
    if not session_name or session_name not in active_sessions:
        return jsonify({"error": "Session not found or not loaded"}), 400
    
    if not message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    
    session = active_sessions[session_name]
    response = session.query(message)
    
    return jsonify({
        "success": True,
        "analysis": response["analysis"],
        "commands": response["commands"]
    })


@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Execute a shell command."""
    data = request.json
    session_name = data.get("session")
    command = data.get("command", "")
    
    if not session_name or session_name not in active_sessions:
        return jsonify({"error": "Session not found or not loaded"}), 400
    
    if not command.strip():
        return jsonify({"error": "Command cannot be empty"}), 400
    
    session = active_sessions[session_name]
    output = session.run_command(command)
    
    return jsonify({
        "success": True,
        "command": command,
        "output": output
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_output():
    """Ask EVA to analyze the last command output."""
    data = request.json
    session_name = data.get("session")
    
    if not session_name or session_name not in active_sessions:
        return jsonify({"error": "Session not found or not loaded"}), 400
    
    session = active_sessions[session_name]
    response = session.analyze_output()
    
    return jsonify({
        "success": True,
        "analysis": response["analysis"],
        "commands": response["commands"]
    })


@app.route('/api/upload', methods=['POST'])
def upload():
    """Upload a file to image hosting services."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Save temporarily
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    try:
        result = upload_file(temp_path)
        os.remove(temp_path)
        return jsonify(result)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500


@app.route('/api/backends', methods=['GET'])
def list_backends():
    """List available AI backends."""
    backends = [
        {
            "id": "demo",
            "name": "Demo Mode",
            "description": "Simulated responses for testing the interface",
            "available": True
        },
        {
            "id": "ollama",
            "name": "Ollama (WhiteRabbit-Neo)",
            "description": "Local AI model - requires Ollama installed",
            "available": check_ollama_available()
        },
        {
            "id": "gpt",
            "name": "OpenAI GPT",
            "description": "OpenAI's GPT model - requires API key",
            "available": get_openai_key() is not None
        },
        {
            "id": "g4f",
            "name": "G4F.dev",
            "description": "Free GPT endpoint via g4f.dev",
            "available": True
        },
        {
            "id": "api",
            "name": "Custom API",
            "description": f"Custom endpoint: {API_ENDPOINT}",
            "available": API_ENDPOINT != "NOT_SET"
        }
    ]
    return jsonify({"backends": backends})


@app.route('/api/config/openai-key', methods=['POST'])
def set_api_key():
    """Set the OpenAI API key."""
    data = request.json
    key = data.get("key", "").strip()
    
    if not key:
        return jsonify({"error": "API key cannot be empty"}), 400
    
    set_openai_key(key)
    return jsonify({"success": True, "message": "OpenAI API key saved"})


@app.route('/api/config/openai-key', methods=['GET'])
def check_api_key():
    """Check if OpenAI API key is configured."""
    key = get_openai_key()
    return jsonify({"configured": key is not None})


def check_ollama_available():
    """Check if Ollama is installed and running."""
    try:
        result = subprocess.run(["which", "ollama"], capture_output=True)
        return result.returncode == 0
    except:
        return False


# ================= STATIC FILES =================

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12000, debug=False, use_reloader=False)
