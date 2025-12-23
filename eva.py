#!/usr/bin/env python3
# made by:    _    ____   ____    _    _   _  ____ _____ _     ___                                                              
#▄████▄ █████▄  ▄█████ ▄████▄ ███  ██  ▄████  ██████ ██     ▄████▄ 
#██▄▄██ ██▄▄██▄ ██     ██▄▄██ ██ ▀▄██ ██  ▄▄▄ ██▄▄   ██     ██  ██ 
#██  ██ ██   ██ ▀█████ ██  ██ ██   ██  ▀███▀  ██▄▄▄▄ ██████ ▀████▀ 
# ---------------------------------------------------------------------                                                                                                             
import os, sys, json, subprocess, signal, re, time, termios, tty
from pathlib import Path
import requests

# ============ Check modules, and autoinstall if not present ============
try:
    from colorama import Fore, Style, init
    import openai 
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "colorama"])
    subprocess.run([sys.executable, "-m", "pip", "install", "openai"])
    from colorama import Fore, Style, init
    from openai import OpenAI


init(autoreset=True)

# ================= CONFIG =================
API_ENDPOINT = "NOT_SET" # <--- change to your desired endpoint if needed
openai.api_base = "https://g4f.dev/v1"
openai.api_key = "jl/JIooPPOcQoHgyW65Mhg13TbIB6CgxcRpJdxMfPRPHZD0oYwuFP29tW4PbkSSxr4U0mqe5kGb5RHVVWAVDgEIWhxujkxyDLRnC7j/PdUOY6UXX/WLrjd3RymPB3WQCGSH7G81iAFFXADpK9Arx8tBUPTNSCUBEw+H4/MyHiYAKlR12uEWHUE+6+8Qd6zEUoqa8VyZ0ZfGIS1BJU5MlXQ3C3vs3zTmP480uFMnvUlh/jCUJUuNlcXQu0ghVtgl1nJuFzMbQLqXUbWV8W9Fu13MChcL3udNczGcRzyteSnBiOOtzZuEU7prf/s/RmhAQ3bKMAFR+JMsmmvFMtyJcPqoXGezzr7GugZTtj6mexsmv84sUr4Js7K9UmJdtF9RmVbrY7UC45XwXcIUm0bpm660Nvn/rPASgSBG6LV5YbWKpq4J9djWApUYLNrY3qvUHs9/5bD0riXOpTYQTE2lOAZEraWcAgBgGeeyQwV/+lpwoihKUk8c9/lhwlMHzZ54e+0j7GHl24aLKlovQXHyUCaQNCTuR4yAzYPc5TTR/gROfE0JQpnZZMLqpIy108GDvLQ6iLxkvfA9zyFReKipUtFWAWMPE0fngAh3BvlZrN3f9DE1qIPmLIwAvBRjCVdHUoHfpp8Z8TbSMAov3G0V6hRYtuIVYieRaT3w6vKH0my0="
OLLAMA_MODEL = "jimscard/whiterabbit-neo:latest" # recommended ollama model
CONFIG_DIR = Path.home() / ".config" / "eva" # Path to save EVA files
SESSIONS_DIR = CONFIG_DIR / "sessions" 
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
username = os.getlogin()
ENV_PATH = Path(".env")

# All sessions will be stored on $HOME/.config/eva/sessions/*.json 

# ═══════════════════════════════════════════════════════════════
#  :: Utilities
#  Utility functions such as ApiKEY verifier and signal handler
# ═══════════════════════════════════════════════════════════════
def checkAPI():
	if API_ENDPOINT == "NOT_SET":
		print(Fore.RED + "\nNo custom API set. Please configure in source code at API_ENPOINT")
		sys.exit(0)


def checkOpenAIKey():
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
    os.system("clear")
    cyber("OpenAI key not found! :: Please insert it below", color=Fore.RED)
    print("\nYour OpenAI API key will be stored locally in .env\n")
    key = input("#key > ").strip()
    if not key:
        print(Fore.RED + "\nNo key provided. Aborting.")
        sys.exit(1)
    with open(ENV_PATH, "a") as f:
        f.write(f"\nOPENAI_API_KEY={key}\n")
    os.environ["OPENAI_API_KEY"] = key
    print(Fore.GREEN + "\n✔ OpenAI API key saved successfully.")
    time.sleep(1)
    return key

def ctrl_c_handler(signum, frame):
    print(Fore.RED + "\n// 🜂 Command interrupted ")

signal.signal(signal.SIGINT, ctrl_c_handler)
       
def clear():
    os.system("clear")


# ════════════════════
#  :: UI FUNCTIONS
# ════════════════════
def cyber(msg="", width=50, color=Fore.GREEN):
    """
    Stylized output in a centered scifi box.
    :param msg: message
    :param width: width
    :param color: Ccolor
    """
    width = int(width)
    print(color + "╔" + "═" * width + "╗")
    if msg:
        msg_line = f"  {msg}  "
        padding = width - len(msg_line)
        left_pad = padding // 2
        right_pad = padding - left_pad
        print(color + "║" + " " * left_pad + msg_line + " " * right_pad + "║")
    print(color + "╚" + "═" * width + "╝")
    print(Style.RESET_ALL)


    
def banner():
    clear() 
    print(Fore.CYAN + r"""
╔═════════════════════════════════════════════╗
║                                             ║
║  ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░    ║
║  ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░   ║
║  ░▒▓█▓▒░       ░▒▓█▓▒▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░   ║
║  ░▒▓██████▓▒░  ░▒▓█▓▒▒▓█▓▒░░▒▓████████▓▒░   ║
║  ░▒▓█▓▒░        ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░   ║
║  ░▒▓█▓▒░        ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░   ║
║  ░▒▓████████▓▒░  ░▒▓██▓▒░  ░▒▓█▓▒░░▒▓█▓▒░   ║
║                       Exploit Vector Agent  ║
║                                             ║
║ ᴍᴀᴅᴇ ʙʏ: 𝝺𝗿𝗰𝗮𝗻𝗴𝗲𝗹𝗼  ​                     ║      
╚═════════════════════════════════════════════╝
""")

# ╔═════════░░░═════════╗
# ░░░   Query input   ░░░
# ╚═════════░░░═════════╝
def raw_input(prompt=""):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = ""
    try:
        tty.setcbreak(fd)
        print(prompt, end="", flush=True)
        while True:
            ch = sys.stdin.read(1)
            if ch in ("\n", "\r"):
                print()
                return buf
            elif ch in ("\x7f", "\x08"):
                if buf:
                    buf = buf[:-1]
                    print("\b \b", end="", flush=True)
            elif ch == "\x03":
                raise KeyboardInterrupt
            else:
                buf += ch
                print(ch, end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ╔═════════░░░═════════╗
# ░░░ Control utilies ░░░
# ╚═════════░░░═════════╝

def menu(title, options):
    idx = 0
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            os.system("clear")
            cyber(title)
            for i, opt in enumerate(options):
                prefix = "→ " if i == idx else "  "
                print(prefix + opt)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                sys.stdin.read(1)
                arrow = sys.stdin.read(1)
                if arrow == "A":
                    idx = (idx - 1) % len(options)
                elif arrow == "B":
                    idx = (idx + 1) % len(options)
            elif ch in ("\n", "\r"):
                return idx
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ╔═════════░░░═════════╗
# ░░░ JSON utility func ░░░
# ──────────░░░─────────
# Handles response if 
# not proper JSON
# ╚═════════░░░═════════╝

def extract_json_anywhere(raw: str, depth=0):
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
# =========================================================================================== 
# ==== EVA PROMPT BUILDING: adapt accordingly as you wish ================
# =========================================================================================== 
def build_prompt(user_msg, last_output):
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

def graceful_exit():
    cyber("EVA OFFLINE :: SESSION IS SAVED", color=Fore.RED)
    print(Fore.YELLOW + "🜂  E x i t i n g  E V A ...")
    time.sleep(2.5)
    clear()
    sys.exit(0)


def normalize_response(resp):
    if not isinstance(resp, dict):
        return {"analysis": "⚠️ Invalid LLM output.", "commands": []}
    return {
        "analysis": resp.get("analysis", "⚠️ Error with model response, please ask again."),
        "commands": resp.get("commands", [])
    }

# +-------------------------------------------+
# | LLM CLASS    -██                          |
# | AI handling logic goes here               |
# +-------------------------------------------+

class LLM:
    def __init__(self, backend):
        self.backend = backend
        self.history = []
        
        
    def query(self, user_msg, last_output=""):
        prompt = build_prompt(user_msg, last_output)

        self.history.append({
            "role": "user",
            "content": prompt
        })

        raw = ""

        # ================= OLLAMA =================
        if self.backend == "ollama":
            p = subprocess.run(
                ["ollama", "run", OLLAMA_MODEL],
                input=prompt,
                text=True,
                capture_output=True
            )
            raw = p.stdout
        
        # ================= G4F.DEV =================
        elif self.backend == "g4f":
            try:
                r = openai.ChatCompletion.create(
                model="gpt-5-1-instant",
                messages=self.history )
                raw = r.get('choices', [{}])[0].get('message', {}).get('content', "[ <!> No response detected ]")
            except Exception:
                print(Fore.YELLOW + f"⚠️ Error with backend [G4F]:\n{Fore.RED}{e}")
                raw = ""

        # ================= CUSTOM API =================
        elif self.backend == "api":
            r = requests.post(
                API_ENDPOINT,
                json={"conversation": self.history},
                timeout=None
            )
            raw = r.text

        # ================= OPENAI GPT =================
        elif self.backend == "gpt":
            openai.api_key = os.environ["OPENAI_API_KEY"]
            try:
                completion = openai.chat.completions.create(
                    model="gpt-5",
                    messages=self.history
                )
                raw = completion.choices[0].message.content

            except Exception as e:
                # ---- fallback GPT-4.1 ----
                try:
                    completion = openai.chat.completions.create(
                        model="gpt-4.1",
                        messages=self.history
                    )
                    raw = completion.choices[0].message.content
                except Exception:
                    print(Fore.RED + f"⚠️ Error querying OpenAI GPTX: {e}")
                    raw = ""

        # ================= JSON EXTRACTION =================
        data = extract_json_anywhere(raw)
    
        if not data:
            data = {
                "analysis": "⚠️ Error parsing model response. Please ask again.",
                "commands": []
            }

        data = normalize_response(data)

        self.history.append({
            "role": "assistant",
            "content": raw
        })

        return data

# +-------------------------------------------+
# | Main core  -██                            |
# | Handler for Eva utilities and             |
# | Initialization and session manag          |
# +-------------------------------------------+


class Eva:
    def __init__(self, session_path, backend):
        self.session_path = session_path
        self.last_output = ""
        self.backend = backend
        self.memory = {
          "backend": backend,
          "timeline": []
        }   
        if session_path.exists():
            self.memory = json.loads(session_path.read_text())
            self.backend = self.memory.get("backend", backend)
        
        self.model = LLM(self.backend)
    def save(self):
        self.session_path.write_text(json.dumps(self.memory, indent=2))
    def change_model_menu(self):
            """
            Model menu during session
            """
            options = [
                f"Use WhiteRabbit-Neo LLM locally {'::[SELECTED]' if self.backend=='ollama' else ''}",
                f"Use OpenAI GPT-5 {'::[SELECTED]' if self.backend=='gpt' else ''}",
                f"Use G4F.dev {'::[SELECTED]' if self.backend=='gpt' else ''}",

                f"Use Custom API endpoint [{API_ENDPOINT}] {'::[SELECTED]' if self.backend=='api' else ''}"
            ]
            sel = menu("CHANGE BACKEND", options)
            if sel == 0:
                self.backend = "ollama"
                self.memory["backend"] = self.backend
                self.save()
            elif sel == 1:
                self.backend = "gpt"
                checkOpenAIKey()
                self.memory["backend"] = self.backend
                self.save()
            elif sel == 2:
                self.backend = "g4f"
                self.memory["backend"] = self.backend
                self.save()                
            elif sel == 3:
                self.backend = "api"
                checkAPI()
                self.memory["backend"] = self.backend
                self.save()
            self.model = LLM(self.backend)

    def run_command(self, cmd):
        cyber(f"EXECUTING → {cmd}")
        proc = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid
        )
        out = ""
        try:
            for line in proc.stdout:
                print(line, end="")
                out += line
        except KeyboardInterrupt:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            print(Fore.RED + "\n/// 🜂 Command stopped by user.")
        self.last_output = out
        self.memory["timeline"].append({
            "type": "command",
            "cmd": cmd,
            "output": out
        })
        self.save()
        self.save()

    def chat(self):
        os.system("clear")
        cyber(":: EVA ONLINE :: ")
        print(Fore.GREEN + "ᐉ ˹E˼xploit ˹V˼ector ˹A˼gent :⦀: Current Model: " + Fore.YELLOW + self.backend)
        print(Fore.RED + "/// type /exit to quit the program anytime")
        print(Fore.RED + "/// type /model to change current model")
        print(Fore.RED + "/// type /menu to go back to sessions menu\n\n")
        for item in self.memory["timeline"]:
            if item["type"] == "user":
                print(Fore.GREEN + f"{username.upper()} > {item['content']}\n")

            elif item["type"] == "analysis":
                cyber("ANALYSIS", color=Fore.MAGENTA)
                print(item["content"] + "\n")

            elif item["type"] == "command":
                cyber(f"EXECUTED → {item['cmd']}", color=Fore.CYAN)
                print(item["output"] + "\n")

        while True:
            user = raw_input(Fore.GREEN + f"\n{username.upper()} > ")
            if user.lower() in ("exit", "quit", "q"):
                self.save()
                graceful_exit()
            if user.lower() in ("menu", "/menu"):
                return main()
            if user.lower() in ("model", "/model"):
                self.change_model_menu()
                os.system("clear")
                cyber(":: EVA ONLINE :: ")
                print(Fore.GREEN + "ᐉ ˹E˼xploit ˹V˼ector ˹A˼gent :⦀: Current Model: " + Fore.YELLOW + self.backend)
                print(Fore.RED + "/// type /exit to quit the program anytime")
                print(Fore.RED + "/// type /model to change current model")
                print(Fore.RED + "/// type /menu to go back to sessions menu\n\n")
                for item in self.memory["timeline"]:
                    if item["type"] == "user":
                        print(Fore.GREEN + f"{username.upper()} > {item['content']}\n")

                    elif item["type"] == "analysis":
                        cyber("ANALYSIS", color=Fore.MAGENTA)
                        print(item["content"] + "\n")

                    elif item["type"] == "command":
                        cyber(f"EXECUTED → {item['cmd']}", color=Fore.CYAN)
                        print(item["output"] + "\n")
                continue

            self.memory["timeline"].append({
                "type": "user",
                "content": user
            })
            self.save()
            resp = self.model.query(user, self.last_output)
            self.memory["timeline"].append({
                "type": "analysis",
                "content": resp["analysis"]
            })
            self.save()
            cyber("ANALYSIS",color=Fore.MAGENTA)
            print(resp["analysis"])
            break_outer = False
            for cmd in resp["commands"]:
   
                while True:
                    choice = raw_input(
                        f"\n> {cmd}\n[R]un | [S]kip | [A]sk | [Q]uit |\n\n> "
                    ).strip().lower()

                    if choice == "r":
                        self.run_command(cmd)
                        resp = self.model.query(
                            "Analyze the previous command output and continue.",
                            self.last_output
                        )
                        cyber("ANALYSIS", color=Fore.MAGENTA)
                        print(resp["analysis"])
                        break  

                    elif choice == "a":
                      break_outer = True
                      break

                    elif choice == "s":
                        break   

                    elif choice == "q":
                        self.save()
                        graceful_exit()

                    else:
                        print("// 🜂 Not a valid input, please type R, S, A or Q.")
                if break_outer:
                  break
            self.save()

# ================= STARTUP OF EVA here =================
def command_exists(cmd):
    return subprocess.call(
        ["which", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0

def ollama_running():
    try:
        output = subprocess.check_output(['ollama', 'list'], stderr=subprocess.STDOUT, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if "server not responding" in e.output.lower():
            return False
        return False

def start_ollama():
    clear()
    print("\n\n\n")
    print(Fore.YELLOW + "🜂 OLLAMA NOT RUNNING :: Starting for you...\n\n")

    with open(os.devnull, 'w') as DEVNULL:
        subprocess.Popen(
            ['ollama', 'serve'],
            stdout=DEVNULL,
            stderr=DEVNULL,
            stdin=DEVNULL,
            close_fds=True,
            start_new_session=True   
        )

    time.sleep(3)
def model_exists():
    r = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True
    )
    return OLLAMA_MODEL in r.stdout

def main():
    banner()
    print(Fore.RED + """
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
➤ THIS TOOL IS FOR:
- CTFs
- LABS
- SYSTEMS YOU OWN
🜂 UNAUTHORIZED USE IS ILLEGAL
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
""")

    if input("Do you have authorization to proceed with this tool? (yes/no): ").lower() != "yes":
        sys.exit()

    sessions = list(SESSIONS_DIR.glob("*.json"))
    opts = [f"[{i+1}] {s.stem}" for i, s in enumerate(sessions)]
    opts.append("[+] NEW SESSION")

    sel = menu("EVA SESSIONS", opts)

    # =========================
    # GETS EXISTING SESSION
    # =========================
    if sel < len(sessions):
        session = sessions[sel]
        data = json.loads(session.read_text())
        backend = data.get("backend", "ollama")

        Eva(session, backend).chat()
        return

    # =========================
    # NEW SESSION
    # =========================
    model = menu(
        "SELECT BACKEND",
        [
            "< GO BACK",
            "Use WhiteRabbit-Neo LLM locally (recommended)",
            "GPT-5 (Needs OpenAI ApiKey)",
            "G4F.dev (Free API endpoint with gpt-5.1)",
            "Use Custom API endpoint (Please check configs to set your own endpoint)"
        ]
    )

    if model == 0:
        return main()

    if model == 1:
        backend = "ollama"

        if not command_exists("ollama"):
            clear()
            cyber("// Ollama is not installed. Install it first.", color=Fore.RED)
            time.sleep(3)
            return main()
        if not ollama_running():
            start_ollama()

        if not model_exists():
            clear()
            pull = menu(f"Model {OLLAMA_MODEL} not found. Pull it?", ["Yes", "No"])
            if pull == 0:
                subprocess.run(["ollama", "pull", OLLAMA_MODEL])
            else:
                return main()

    elif model == 2:
        backend = "gpt"
        checkOpenAIKey()
    elif model == 3:
        backend = "g4f"
    elif model == 4:
        backend = "api"
        checkAPI()
    else:
        return main()

    session = SESSIONS_DIR / f"session{len(sessions) + 1}.json"
    Eva(session, backend).chat()
    
    
if __name__ == "__main__":
    main()
