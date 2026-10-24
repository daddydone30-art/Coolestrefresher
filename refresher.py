import requests
import json
import os

# Configuration file to store your cookie safely
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"cookie": "YOUR_INITIAL_ROBLOSECURITY_HERE"}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def refresh_roblox_cookie():
    config = load_config()
    old_cookie = config.get("cookie")

    if not old_cookie or old_cookie == "YOUR_INITIAL_ROBLOSECURITY_HERE":
        print("[-] Error: Please set a valid .ROBLOSECURITY cookie in config.json first.")
        return

    # Step 1: Request a CSRF token
    headers = {
        "Cookie": f".ROBLOSECURITY={old_cookie}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.roblox.com/"
    }

    print("[*] Attempting to fetch CSRF token...")
    csrf_response = requests.post("https://auth.roblox.com/v2/logout", headers=headers)
    
    # Roblox usually returns a 403 with the x-csrf-token header even if unauthenticated/logged out, 
    # but for a valid cookie, it provides the token we need.
    csrf_token = csrf_response.headers.get("x-csrf-token")

    if not csrf_token:
        print("[-] Failed to retrieve CSRF token. Your cookie might already be expired or invalid.")
        return

    # Step 2: Request Authentication Ticket
    ticket_headers = {
        "Cookie": f".ROBLOSECURITY={old_cookie}",
        "X-CSRF-TOKEN": csrf_token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.roblox.com/"
    }

    print("[*] Requesting authentication ticket...")
    ticket_response = requests.post("https://auth.roblox.com/v1/authentication-ticket", headers=ticket_headers)
    
    auth_ticket = ticket_response.headers.get("rbx-authentication-ticket")

    if not auth_ticket:
        print(f"[-] Failed to get authentication ticket. Response: {ticket_response.text}")
        return

    # Step 3: Redeem Ticket for New Cookie
    redeem_headers = {
        "RBXAuthenticationNegotiation": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.roblox.com/"
    }
    
    payload = {
        "authenticationTicket": auth_ticket
    }

    print("[*] Redeeming ticket for a new cookie...")
    redeem_response = requests.post("https://auth.roblox.com/v1/authentication-ticket/redeem", headers=redeem_headers, json=payload)

    # Extract the new .ROBLOSECURITY from set-cookie headers
    set_cookie_header = redeem_response.headers.get("Set-Cookie", "")
    
    if ".ROBLOSECURITY=" in set_cookie_header:
        # Parse the new cookie value out of the header string
        try:
            new_cookie_part = set_cookie_header.split(".ROBLOSECURITY=")[1]
            new_cookie = new_cookie_part.split(";")[0]
            
            # Save the new cookie
            config["cookie"] = new_cookie
            save_config(config)
            print("[+] SUCCESS: Cookie refreshed successfully and saved to config.json!")
        except Exception as e:
            print(f"[-] Failed to parse new cookie from header: {e}")
    else:
        print(f"[-] Failed to redeem ticket. Response: {redeem_response.text}")

if __name__ == "__main__":
    refresh_roblox_cookie()
