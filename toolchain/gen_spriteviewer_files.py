import sys
import os
import json
import re
import subprocess

p = os.path.join
pose = re.compile(r"([0-9]+)\.png")
face = re.compile(r"[0-9]+_([0-9]+)\.png")

def call_ianalysis(i1, i2):
    p = subprocess.check_output([os.path.join(os.path.dirname(__file__), "ianalysis"), i1, i2])
    return json.loads(p.decode("utf-8"))

def lookup_cid(cid, poseid):
    return next(filter(lambda x: x.chara_id == cid and x.pose == poseid, chara_face_position))

def svx(dir):
    print("svx({0}) . . . ".format(dir), end="")
    poses = []
    files = os.listdir(dir)
    cid = int(os.path.basename(dir))

    sprite_list = filter(lambda x: os.path.isfile(p(dir, x)) and pose.match(x), files)
    for file in sprite_list:
        print(file, end=" ")
        pose_int = int(pose.findall(file)[0])
        faces = []
        one_face_filename = None

        face_list = filter(lambda x: os.path.isfile(p(dir, x)) and x.startswith(str(pose_int) + "_"), files)
        for face_name in face_list:
            faces.append(int(face.findall(face_name)[0]))
            one_face_filename = face_name

        if faces:
            print(faces, end=" ")
            #result = [0, 0]
            result = call_ianalysis(p(dir, file), p(dir, one_face_filename))
            poses.append({"id": pose_int,
                          "face_list": faces,
                          "position": result})

    payload = list(poses)

    with open(p(dir, "svx.json"), "w") as file:
        file.write("POSE_LIST(")
        json.dump(payload, file)
        file.write(");")
    print()

def walk(dir):
    for d in os.listdir(dir):
        if os.path.isdir(p(dir, d)):
            svx(p(dir, d))

if __name__ == '__main__':
    walk(sys.argv[1])