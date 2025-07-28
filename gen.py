from kiteconnect import KiteConnect

kite = KiteConnect(api_key="q3bnfchthjyxf8rc")
data = kite.generate_session("DV5gTk3Wv4MnjnJ9fTfz1WV9CHyWpkMb",api_secret="oi7vtyd9k9mteb8raviad10b1h5srub4")
print(data["access_token"])
session = kite.set_access_token(data["access_token"])
print("Session created successfully:", session)
