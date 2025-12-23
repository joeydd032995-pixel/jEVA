import os
import sys
import requests
import mimetypes
import re
import time
from requests_toolbelt import MultipartEncoder

def upload_file(filepath: str) -> str:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)
    
    with open(filepath, "rb") as f:
        data = f.read()
    
    # Determine file extension and MIME type
    ext = filepath.split(".")[-1] or "jpg"
    mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
    
    providers = [
        ("imgbb.com", lambda: upload_to_imgbb(filepath, data, ext)),
        ("telegra.ph", lambda: upload_to_telegra(data, ext, mime)),
        ("catbox.moe", lambda: upload_to_catbox(data, ext, mime)),
    ]
    
    for provider_name, upload_func in providers:
        try:
            url = upload_func()
            return url
        except Exception as e:
            print(f"Failed to upload to {provider_name}: {e}")
            continue
    
    raise Exception("All upload providers failed")

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    try:
        url = upload_file(filepath)
        print(url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
