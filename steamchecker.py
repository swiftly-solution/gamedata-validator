
import time
from SteamInfoRetriever import AppInfoRetriever
import hashlib
import requests

app_info_retriever = AppInfoRetriever()
app_info_retriever.login()
s = ""

def get_file_signature(url, algorithm='sha256'):
    hash_obj = hashlib.new(algorithm)
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()[0:16:1]

def GetSignatureJsonSignature():
    return get_file_signature("https://raw.githubusercontent.com/swiftly-solution/swiftlys2/refs/heads/master/plugin_files/gamedata/cs2/core/signatures.jsonc")

def CheckGameUpdates(app_id):
    global build_id

    try:
        api_data = app_info_retriever.retrieve_app_info(app_id)
    except:
        return False

    build_id = str(api_data['apps'][f'{app_id}']['depots']['branches']['public']['buildid'])
    gid_2347771 = str(api_data['apps'][f'{app_id}']['depots']['2347771']['manifests']['public']['gid'])
    gid_2347773 = str(api_data['apps'][f'{app_id}']['depots']['2347773']['manifests']['public']['gid'])
    
    update_signature = f"{build_id}|{gid_2347771}|{gid_2347773}|{GetSignatureJsonSignature()}"

    try:
        with open(f"public{app_id}.txt", "r") as f:
            file_info = f.read()
    except FileNotFoundError:
        file_info = ""

    updated_depots = []
    if gid_2347771 not in file_info:
        updated_depots.append('2347771')
    if gid_2347773 not in file_info:
        updated_depots.append('2347773')

    if updated_depots:
        try:
            with open(f"public{app_id}.txt", "a") as f:
                f.write(f"\n{update_signature}")
        except:
            return []

    return updated_depots

def GetSignature():
    global s
    if s != "":
        return s

    s = build_id + "_" + str(int(time.time()))
    return s