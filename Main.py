import streamlit as st
import requests
import re
import hashlib
import os
import random
import string
import base64
import time
import socket
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

# App Config
st.set_page_config(page_title="OSINT Utility Tool", page_icon="⚡", layout="centered")
st.title("⚡ OSINT & Utility Command Center")
st.markdown("Type `/help` to see all available commands.")

# State init
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tm_email" not in st.session_state:
    st.session_state.tm_email = ""
if "tm_sid" not in st.session_state:
    st.session_state.tm_sid = ""

def get_cmd(text):
    text = text.strip()
    cmds = {"/sub":"SUB","/whois":"WHOIS","/fake":"FAKE","/encode":"ENC","/decode":"DEC",
            "/pass":"PASS","/shodan":"SHODAN","/mac":"MAC","/scan":"SCAN","/age":"AGE",
            "/tempmail":"TM","/inbox":"TMIN","/qr":"QR","/speak":"TTS","/pwned":"PWNED",
            "/short":"SHORT","/ping":"PING","/help":"HELP","/myip":"MYIP","/vt":"VT",
            "/ipinfo":"IPINFO","/urlscan":"URLSCAN","/serp":"SERP"}
    for k, v in cmds.items():
        if text.startswith(k): return v
    if re.match(r"^\+?[0-9]{10,15}$", text.replace(" ","").replace("-","")): return "PHONE"
    return "UNK"

def process_command(cmd, data):
    data = data.strip()
    try:
        if cmd == "HELP":
            return "🔹 **Commands:**\n`/ping domain`, `/sub domain`, `/whois domain`, `/shodan target`, `/scan target`, `/mac address`, `/ipinfo target`, `/myip`, `/vt domain`, `/urlscan url`, `/serp query`, `/pwned pass`, `/pass`, `/encode text`, `/decode base64`, `/fake`, `/tempmail`, `/inbox`, `/qr text`, `/speak text`, `/short url`, `/age YYYY-MM-DD`\n*(Or just type a Phone Number with country code)*"

        req_data = ["QR","TTS","ENC","DEC","PWNED","SHORT","PING","SUB","WHOIS","MAC","SHODAN","SCAN","AGE","VT","IPINFO","URLSCAN","SERP"]
        if cmd in req_data and not data:
            return "⚠️ Please provide a target or text after the command. (Example: `/ping google.com`)"

        if cmd == "PHONE":
            parsed = phonenumbers.parse(data, None)
            if not phonenumbers.is_valid_number(parsed): return "❌ Invalid number format. Use Country Code (e.g. +91...)"
            country = geocoder.description_for_number(parsed, "en")
            network = carrier.name_for_number(parsed, "en")
            return f"📞 **Phone Info:**\nCountry: {country}\nCarrier: {network}"
            
        elif cmd == "QR":
            qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=512x512&data=" + quote(data)
            return f"✅ **QR Code Generated:**\n[Click here to view or download]({qr_url})"
            
        elif cmd == "TTS":
            tts = gTTS(data, lang='bn')
            fname = f"audio_{int(time.time())}.mp3"
            tts.save(fname)
            return f"✅ **Audio Saved locally as:** `{fname}`"
            
        elif cmd == "FAKE":
            return f"👤 **Fake Identity:**\nName: {fake.name()}\nEmail: {fake.email()}\nPhone: {fake.phone_number()}\nAddress: {fake.address()}\nCard: {fake.credit_card_full()}"
            
        elif cmd == "PASS":
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            pwd = ''.join(random.choice(chars) for _ in range(16))
            return f"🔐 **Secure Password:** `{pwd}`"
            
        elif cmd == "ENC":
            return "🔒 **Encoded:**\n`" + base64.b64encode(data.encode()).decode() + "`"
            
        elif cmd == "DEC":
            return "🔓 **Decoded:**\n`" + base64.b64decode(data.encode()).decode() + "`"
            
        elif cmd == "PWNED":
            h = hashlib.sha1(data.encode()).hexdigest().upper()
            r = requests.get("https://api.pwnedpasswords.com/range/" + h[:5], timeout=10)
            c = 0
            for line in r.text.splitlines():
                if line.startswith(h[5:]): 
                    c = int(line.split(':')[1]); break
            return f"⚠️ **Leaked:** {c} times!" if c else "✅ **Safe password!**"
            
        elif cmd == "SHORT":
            r = requests.get("https://tinyurl.com/api-create.php?url=" + quote(data), timeout=10)
            return f"🔗 **Short URL:** {r.text}"
            
        elif cmd == "PING":
            target = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            st_time = time.time()
            requests.get("http://" + target, timeout=10)
            ms = int((time.time()-st_time)*1000)
            return f"📡 **{target} is UP!** ({ms}ms)"
            
        elif cmd == "SUB":
            domain = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            r = requests.get("https://crt.sh/?q=%." + domain + "&output=json", timeout=30)
            if r.status_code != 200 or not r.text: return "❌ No subdomains found or API blocked."
            subs = sorted(set([e['name_value'] for e in r.json()]))[:20]
            return "**Subdomains:**\n" + "\n".join(subs) if subs else "❌ No subdomains found"
            
        elif cmd == "WHOIS":
            domain = data.replace("http://","").replace("https://","").split('/')[0].split(':')[0]
            r = requests.get("https://api.hackertarget.com/whois/?q=" + domain, timeout=20)
            
