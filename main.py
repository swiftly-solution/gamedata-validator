import json
import subprocess
import platform
import time
import commentjson
import git
import s2binlib
import shutil
import argparse
from os import path, makedirs
from dotenv import load_dotenv
from steamchecker import CheckGameUpdates, GetSignature
from discord_notifier import notify_vfunc_results, notify_pattern_scan_results

load_dotenv()

def download_depot(depot_id, branch='public'):
    executable = './data/DepotDownloader' + ('.exe' if platform.system() == 'Windows' else '')

    args = ['-app', '730', '-depot', str(depot_id), '-branch', branch, '-dir', f"{workspace_name}/binaries", '-filelist', './data/files.txt']

    command = [executable] + args
    print(f"Running command for depot {depot_id}: {' '.join(command)}")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()

    print(f"Output from Depot {depot_id}:")
    print(stdout.decode())

    if stderr:
        print(f"Error from Depot {depot_id}:")
        print(stderr.decode())

def download_depots(branch='public'):
  download_depot(2347771, branch)
  download_depot(2347773, branch)

def download_swiftlys2():
  repo = git.Repo.clone_from(
    'https://github.com/swiftly-solution/swiftlys2.git',
    workspace_name + '/swiftlys2'
  )

def dump_vfunc_counts(os):
    outputs = []
    with open("data/classes.json", "r") as f:
        classes = json.load(f)
        for class_info in classes:
            class_binary_name = class_info["name"]
            for class_name in class_info["classes"]:
                try:
                    table_va = s2binlib.find_vtable_va(class_binary_name, class_name)
                    vfunc_count = s2binlib.get_vfunc_count(class_binary_name, class_name)
                    outputs.append({
                        "class_name": class_name,
                        "vfunc_count": vfunc_count,
                        "va": class_binary_name+"."+hex(table_va),
                        "binary": class_binary_name
                    })
                except Exception as e:
                    print(f"Error finding vtable for {class_name} in {class_binary_name}: {e}")
                    continue

    with open(f"output/{GetSignature()}/vfunc_counts_{os}.json", "w") as f:
        json.dump(outputs, f, indent=4)

    return outputs

def pattern_scan(os, signatures_file=None):
    outputs = []
    if signatures_file is None:
        signatures_file = f"{workspace_name}/swiftlys2/plugin_files/gamedata/cs2/core/signatures.jsonc"
    
    with open(signatures_file, "r") as f:
        signatures = commentjson.load(f, )
        for signature_name, signature in signatures.items():
            match, count = s2binlib.pattern_scan(signature["lib"], signature[os])
            outputs.append({
                "signature": signature_name,
                "va": signature["lib"]+"."+hex(match),
                "count": count
            })

    with open(f"output/{GetSignature()}/signatures_{os}.json", "w") as f:
        json.dump(outputs, f, indent=4)

    return outputs

def commit_and_push_changes(signature):
    try:
        repo = git.Repo('.')

        repo.index.add(['output/*', 'public730.txt'])

        if repo.index.diff("HEAD") or repo.untracked_files:
            commit_message = f"update(results): Validating files for `{signature}`"

            repo.index.commit(commit_message)

            origin = repo.remote(name='origin')
            origin.push()
        else:
            print("No changes to commit")

    except Exception as e:
        print(f"Error committing/pushing changes: {e}")

def CheckUpdate(branch='public', signatures_file=None):
    global workspace_name
    updated_depots = CheckGameUpdates(730, branch)
    if updated_depots:
        workspace_name = "workspace_"+ GetSignature()
        makedirs(f"output/{GetSignature()}", exist_ok=True)
        makedirs(workspace_name +"/swiftlys2", exist_ok=True)

        if not path.exists(workspace_name+"/binaries"):
            makedirs(workspace_name+"/binaries")
            download_depots(branch)

        download_swiftlys2()

        vfunc_results = {}
        scan_results = {}
        for os in ["windows", "linux"]:
            s2binlib.initialize(f"./{workspace_name}/binaries/game", "csgo", os)
            vfunc_results[os] = dump_vfunc_counts(os)
            scan_results[os] = pattern_scan(os, signatures_file)

        notify_vfunc_results(vfunc_results, GetSignature(), branch)
        notify_pattern_scan_results(scan_results, GetSignature(), branch)

        if path.exists("output/latest"):
            shutil.rmtree("output/latest")
        shutil.copytree(f"output/{GetSignature()}", f"output/latest")

        commit_and_push_changes(GetSignature())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gamedata validator for CS2')
    parser.add_argument('--branch', type=str, default='public', help='Game branch to check (default: public)')
    parser.add_argument('--signatures', type=str, default=None, help='Path to custom signatures file')
    args = parser.parse_args()
    
    while True:
        CheckUpdate(branch=args.branch, signatures_file=args.signatures)
        time.sleep(10)