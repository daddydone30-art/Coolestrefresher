from flask import Flask, render_template_string, request, jsonify
import requests
import random

app = Flask(__name__)

# Your Webshare Proxy List loaded directly into the app
PROXIES_LIST = [
    "45.38.107.97:6014:saxqnmup:rgvs7uvqydbm",
    "64.137.96.74:6641:saxqnmup:rgvs7uvqydbm",
    "198.23.243.226:6361:saxqnmup:rgvs7uvqydbm",
    "38.154.185.97:6370:saxqnmup:rgvs7uvqydbm",
    "84.247.60.125:6095:saxqnmup:rgvs7uvqydbm",
    "191.96.254.138:6185:saxqnmup:rgvs7uvqydbm",
    "198.46.161.42:5092:saxqnmup:rgvs7uvqydbm",
    "64.137.10.153:5803:saxqnmup:rgvs7uvqydbm",
    "104.164.49.38:7693:saxqnmup:rgvs7uvqydbm",
    "23.26.71.145:5628:saxqnmup:rgvs7uvqydbm"
]

def get_random_proxy():
    # Format Webshare proxies for python requests: http://username:password@ip:port
    p = random.choice(PROXIES_LIST)
    ip, port, user, pwd = p.split(":")
    proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
    return {
        "http": proxy_url,
        "https": proxy_url
    }

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Roblox Cookie Refresher Dashboard</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 500px; border: 1px solid #334155; }
        h2 { color: #38bdf8; margin-top: 0; }
        textarea { width: 100%; height: 100px; background: #0f172a; border: 1px solid #475569; color: #38bdf8; padding: 10px; border-radius: 6px; resize: none; margin-bottom: 15px; box-sizing: border-box; }
        button { background: #0284c7; color: white; border: none; padding: 12px 20px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px; }
        button:hover { background: #0369a1; }
        #result { margin-top: 15px; padding: 10px; border-radius: 6px; background: #0f172a; word-break: break-all; font-size: 12px; min-height: 40px; border: 1px solid #334155; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Roblox Cookie Refresher</h2>
        <p>Paste your .ROBLOSECURITY cookie below:</p>
        <textarea id="cookieInput" placeholder="_|WARNING:-DO-NOT-SHARE-THIS..."></textarea>
        <button onclick="refreshCookie()">Refresh Cookie Now</button>
        <div id="result">Status: Ready...</div>
    </div>

    <script>
        async function refreshCookie() {
            const cookie = document.getElementById('cookieInput').value.trim();
            const resultDiv = document.getElementById('result');
            if (!cookie) {
                resultDiv.innerText = "Error: Please enter a cookie.";
                return;
            }
            resultDiv.innerText = "Processing request through proxy rotation...";
            
            const response = await fetch('/api/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookie: cookie })
            });
            const data = await response.json();
            if (data.success) {
                resultDiv.innerHTML = `<span style="color: #4ade80;">SUCCESS! New Cookie:</span><br><br>${data.new_cookie}`;
                document.getElementById('cookieInput').value = data.new_cookie;
            } else {
                resultDiv.innerHTML = `<span style="color: #f87171;">FAILED: ${data.error}</span>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    data = request.get_json()
    old_cookie = data.get("cookie")

    if not old_cookie:
        return jsonify({"success": False, "error": "No cookie provided"})

    headers = {
        "Cookie": f".ROBLOSECURITY={old_cookie}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.roblox.com/"
    }

    proxies = get_random_proxy()

    try:
        # Step 1: Get CSRF Token via Proxy
        csrf_res = requests.post("https://auth.roblox.com/v2/logout", headers=headers, proxies=proxies, timeout=15)
        csrf_token = csrf_res.headers.get("x-csrf-token")
        if not csrf_token:
            return jsonify({"success": False, "error": "Invalid or expired cookie (Failed to get CSRF token via proxy)"})

        # Step 2: Get Auth Ticket via Proxy
        ticket_headers = headers.copy()
        ticket_headers["X-CSRF-TOKEN"] = csrf_token
        ticket_res = requests.post("https://auth.roblox.com/v1/authentication-ticket", headers=ticket_headers, proxies=proxies, timeout=15)
        auth_ticket = ticket_res.headers.get("rbx-authentication-ticket")
        if not auth_ticket:
            return jsonify({"success": False, "error": "Failed to generate authentication ticket via proxy"})

        # Step 3: Redeem Ticket via Proxy
        redeem_headers = {
            "RBXAuthenticationNegotiation": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.roblox.com/"
        }
        redeem_res = requests.post("https://auth.roblox.com/v1/authentication-ticket/redeem", headers=redeem_headers, json={"authenticationTicket": auth_ticket}, proxies=proxies, timeout=15)
        
        set_cookie = redeem_res.headers.get("Set-Cookie", "")
        if ".ROBLOSECURITY=" in set_cookie:
            new_cookie = set_cookie.split(".ROBLOSECURITY=")[1].split(";")[0]
            return jsonify({"success": True, "new_cookie": new_cookie})
        else:
            return jsonify({"success": False, "error": "Failed to redeem authentication ticket"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
