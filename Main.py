import streamlit as st
import requests, re, hashlib, os, random, string, base64, time, socket
import phonenumbers
from phonenumbers import geocoder, carrier
from faker import Faker
from gtts import gTTS
from datetime import datetime
from urllib.parse import quote

# ===== API KEYS =====
VT_KEY = "b2059cd3b9c6ca6d84bc11e1d272675454153d92a0dbc54052df99b31c7fd364"
SERP_KEY = "6f75416d78ef4f8b69fa73181136f92625fd25706604b912d6db4d81ce0432b5"
SHODAN_KEY = "f8FhmHfYXrAuHRHT5VdjV3stISGzn39w"
IPINFO_KEY = "c5b71db5f62783"
URLSCAN_KEY = "019e52a8-932a-7662-9885-94e6a4673e31"

fake = Faker()

# Streamlit Page Config
st.set_page_config(page_title="OSINT Utility Tool", page_icon="⚡", layout="centered")
st.title("⚡ OSINT & Utility Command Center")
st.markdown("Type `/help` to see all available commands.")

# Initialize Session State for Chat History and Temp Mail
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tm_email" not in st.session_state:
    st.session_state.tm_email = ""
if "tm_sid" not in st.session_state:
    st.session_state.tm_sid = ""

def get_cmd(t):
    t = t.strip()
    cmds = {"/sub":"SUB","/whois":"WHOIS","/fake":"FAKE","/encode":"ENC","/decode":"DEC","/pass":"PASS","/shodan":"SHODAN","/mac":"MAC","/scan":"SCAN","/age":"AGE","/tempmail":"TM","/inbox":"TMIN","/qr":"QR","/speak":"TTS","/pwned":"PWNED","/short":"SHORT","/ping":"PING","/help":"HELP","/myip":"MYIP","/vt":"VT","/ipinfo":"IPINFO","/urlscan":"URLSCAN","/serp":"SERP"}
    for k, v in cmds.items():
        if t.startswith(k): return v
    if re.match(r"^\+?[0-9]{10,15}$", t.replace(" ","").replace("-","")): return "PHONE"
    return "UNK"

def process_command(cmd, data):
    try:
        if cmd == "HELP":
            return "Commands:\n/sub domain\n/whois domain\n/shodan target\n/scan target\n/mac XX:XX:XX:XX:XX:XX\n/ipinfo target\n/myip\n/vt domain\n/urlscan url\n/serp query\n/pwned pass\n/pass\n/encode text\n/decode base64\n/ping target\n/fake\n/tempmail\n/inbox\n/qr text\n/speak text\n/short url\n/age YYYY-MM-DD\nOr just type a Phone Number with country code."
        
        elif cmd == "PHONE":
            parsed = phonenumbers.parse(data, None)
            if not phonenumbers.is_valid_number(parsed): return "Invalid number"
            country = geocoder.description_for_number(parsed, "en")
            network = carrier.name_for_number(parsed, "en")
            return f"Phone Info:\nValid: Yes\nCountry: {country or 'Unknown'}\nCarrier: {network or 'Unknown'}"
            
        elif cmd == "QR":
            if not data: return "Provide text for QR."
            qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=512x512&data=" + quote(data)
            return f"QR Code Generated:\n{qr_url}\n*(Click the link to view/download)*"
            
        elif cmd == "TTS":
            if not data: return "Provide text to speak."
            tts = gTTS(data, lang='bn')
            fname = f"audio_{int(time.time())}.mp3"
            tts.save(fname)
            return f"Audio generated. File saved as {fname}. (Note: In cloud, downloading audio directly needs extra setup, try using Flet or Termux for direct audio play)."
            
        elif cmd == "FAKE":
            return f"Fake Identity:\nName: {fake.name()}\nEmail: {fake.email()}\nPhone: {fake.phone_number()}\nAddress: {fake.address()}\nCard: {fake.credit_card_full()}"
            
        elif cmd == "PASS":
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            pwd = ''.join(random.choice(chars) for _ in range(16))
            return "Secure Password:\n" + pwd
            
        elif cmd == "ENC":
            return "Encoded:\n" + base64.b64encode(data.encode()).decode()
            
        elif cmd == "DEC":
            return "Decoded:\n" + base64.b64decode(data.encode()).decode()
            
        elif cmd == "PWNED":
            h = hashlib.sha1(data.encode()).hexdigest().upper()
            r = requests.get("https://api.pwnedpasswords.com/range/" + h[:5], timeout=10)
            c = 0
            for line in r.text.splitlines():
                if line.startswith(h[5:]): 
                    c = int(line.split(':')[1]); break
            return f"Leaked {c} times!" if c else "Safe password!"
            
        elif cmd == "SHORT":
            r = requests.get("https://tinyurl.com/api-create.php?url=" + quote(data), timeout=10)
            return "Short URL:\n" + r.text
            
        elif cmd == "PING":
            target = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            st_time = time.time()
            requests.get("http://" + target, timeout=10)
            ms = int((time.time()-st_time)*1000)
            return f"{target} is UP! {ms}ms"
            
        elif cmd == "SUB":
            domain = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            r = requests.get("https://crt.sh/?q=%." + domain + "&output=json", timeout=30)
            subs = sorted(set([e['name_value'] for e in r.json()]))[:20]
            return "Subdomains:\n" + "\n".join(subs) if subs else "No subdomains found"
            
        elif cmd == "WHOIS":
            domain = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            r = requests.get("https://api.hackertarget.com/whois/?q=" + domain, timeout=20)
            return r.text[:3500]
            
        elif cmd == "MAC":
            mac = data.replace("-",":").replace(".",":")
            r = requests.get("https://api.macvendors.com/" + mac, timeout=15)
            return "Vendor: " + r.text if r.status_code == 200 else "Unknown"
            
        elif cmd == "SHODAN":
            target = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', target):
                r = requests.get(f"https://api.shodan.io/shodan/host/{target}?key={SHODAN_KEY}", timeout=15)
            else:
                r = requests.get(f"https://api.shodan.io/dns/resolve?hostnames={target}&key={SHODAN_KEY}", timeout=15)
                if target in r.json(): r = requests.get(f"https://api.shodan.io/shodan/host/{r.json()[target]}?key={SHODAN_KEY}", timeout=15)
                else: return "Cannot resolve"
            if r.status_code == 200:
                d = r.json()
                reply = f"Shodan: {d.get('ip_str','')}\nCountry: {d.get('country_name','')}\nORG: {d.get('org','')}\nOS: {d.get('os','Unknown')}"
                ports = d.get('ports',[])
                if ports: reply += "\nPorts: " + ', '.join(str(p) for p in ports[:10])
                return reply
            return "No data"
            
        elif cmd == "SCAN":
            target = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            ip = socket.gethostbyname(target)
            PORTS = [21,22,23,25,53,80,110,143,443,445,993,995,1433,3306,3389,5432,5900,6379,8080,8443]
            open_ports = []
            for port in PORTS:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((ip, port)) == 0: open_ports.append(port)
                s.close()
            return f"Open ports on {target}: " + ', '.join(str(p) for p in open_ports) if open_ports else "No open ports found"
            
        elif cmd == "AGE":
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"]:
                try: 
                    dob = datetime.strptime(data.strip(), fmt)
                    break
                except: continue
            else: return "Use YYYY-MM-DD"
            age = datetime.today().year - dob.year - ((datetime.today().month, datetime.today().day) < (dob.month, dob.day))
            return f"Age: {age} years"
            
        elif cmd == "VT":
            target = data.replace("http://","").replace("https://","").split('/')[0]
            r = requests.get("https://www.virustotal.com/api/v3/domains/" + target, headers={"x-apikey": VT_KEY}, timeout=30)
            if r.status_code == 200:
                s = r.json()['data']['attributes']['last_analysis_stats']
                return f"VT: Malicious: {s.get('malicious',0)}, Suspicious: {s.get('suspicious',0)}, Harmless: {s.get('harmless',0)}"
            return f"VT Error: {r.status_code}"
            
        elif cmd == "IPINFO":
            target = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            r = requests.get(f"https://ipinfo.io/{target}/json?token={IPINFO_KEY}", timeout=15)
            if r.status_code == 200:
                d = r.json()
                return f"IP: {d.get('ip','')}\nCity: {d.get('city','')}\nRegion: {d.get('region','')}\nCountry: {d.get('country','')}\nORG: {d.get('org','')}"
            return "Not found"
            
        elif cmd == "URLSCAN":
            if not data.startswith("http"): data = "https://" + data
            headers = {"API-Key": URLSCAN_KEY, "Content-Type": "application/json"}
            r = requests.post("https://urlscan.io/api/v1/scan/", json={"url": data, "visibility": "public"}, headers=headers, timeout=60)
            if r.status_code == 200:
                return "Submitted! Result: " + r.json().get('result', '')
            return f"Error: {r.status_code}"
            
        elif cmd == "SERP":
            r = requests.get(f"https://serpapi.com/search?q={quote(data)}&api_key={SERP_KEY}", timeout=30)
            if r.status_code == 200:
                results = r.json().get('organic_results', [])[:5]
                if results:
                    reply = "Results:\n"
                    for res in results: reply += f"{res.get('title','')} - {res.get('link','')}\n"
                    return reply
                return "No results"
            return f"Error: {r.status_code}"
            
        elif cmd == "TM":
            r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address&ip=127.0.0.1&agent=Bot", timeout=30)
            st.session_state.tm_email = r.json().get('email_addr','')
            st.session_state.tm_sid = r.json().get('sid_token','')
            return f"Temp Email: {st.session_state.tm_email}\nUse /inbox to check."
            
        elif cmd == "TMIN":
            if not st.session_state.tm_sid: return "Run /tempmail first"
            r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=get_email_list&sid_token={st.session_state.tm_sid}", timeout=30)
            emails = r.json().get('list',[])
            if emails:
                reply = "Inbox:\n"
                for em in emails[:5]: reply += f"From: {em.get('mail_from','')} - {em.get('mail_subject','')}\n"
                return reply
            return "No emails"
            
        elif cmd == "MYIP":
            ip = requests.get("https://api.ipify.org?format=json", timeout=10).json()['ip']
            return "Server IP: " + ip
            
        else:
            return "Unknown command. Type /help to see the list."
            
    except Exception as e:
        return f"Error during execution: {str(e)}"

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if user_input := st.chat_input("Enter command (e.g. /ping google.com)"):
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process command
    cmd = get_cmd(user_input)
    parts = user_input.split(maxsplit=1)
    data = parts[1] if len(parts) > 1 else ""
    
    with st.spinner("Processing..."):
        response = process_command(cmd, data)

    # Add bot response to state and display
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
