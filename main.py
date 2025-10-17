import json
import s2binlib
import os
import git
import subprocess
import commentjson 

def download_depot(depot_id):
    linux_executable = './data/DepotDownloader.exe'

    args = ['-app', '730', '-depot', str(depot_id), '-dir', 'workspace/binaries', '-filelist', './data/files.txt']

    command = [linux_executable] + args
    print(f"Running command for depot {depot_id}: {' '.join(command)}")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()

    print(f"Output from Depot {depot_id}:")
    print(stdout.decode())

    if stderr:
        print(f"Error from Depot {depot_id}:")
        print(stderr.decode())

def download_depots():
  download_depot(2347771)
  download_depot(2347773)

def download_swiftlys2():
  repo = git.Repo.clone_from(
    'https://github.com/swiftly-solution/swiftlys2.git',
    'workspace/swiftlys2'
  )


def dump_vfunc_counts(os):
  outputs = []
  with open("data/classes.json", "r") as f:
    classes = json.load(f)
    for class_info in classes:
      class_binary_name = class_info["name"]
      for class_name in class_info["classes"]:
        try:
          vtable_va = s2binlib.find_vtable_va(class_binary_name, class_name)
          vfunc_count = s2binlib.get_vfunc_count(class_binary_name, class_name)
          outputs.append({
            "class_name": class_name,
            "vfunc_count": vfunc_count
          })
        except Exception as e:
          print(f"Error finding vtable for {class_name} in {class_binary_name}: {e}")
          continue

  with open(f"output/vfunc_counts_{os}.json", "w") as f:
    json.dump(outputs, f, indent=2)

def pattern_scan(os):
  outputs = []
  with open("workspace/swiftlys2/plugin_files/gamedata/cs2/core/signatures.jsonc", "r") as f:
    signatures = commentjson.load(f, )
    for signature_name, signature in signatures.items():
      match, count = s2binlib.pattern_scan(signature["lib"], signature[os])
      outputs.append({
        "signature": signature_name,
        "va": signature["lib"]+"."+hex(match),
        "count": count
      })
  
  with open(f"output/signatures_{os}.json", "w") as f:
    json.dump(outputs, f, indent=2)

if __name__ == "__main__":
  os.makedirs("output", exist_ok=True)
  os.makedirs("workspace/swiftlys2", exist_ok=True)

  if not os.path.exists("workspace/binaries"):
    os.makedirs("workspace/binaries")
    download_depots()
  if not os.path.exists("workspace/swiftlys2"):
    download_swiftlys2()

  for os in ["windows", "linux"]:
    s2binlib.initialize(f"./workspace/binaries/game", "csgo", os)
    dump_vfunc_counts(os)
    pattern_scan(os)