import numpy as np
import json
from vis_utils.scene.components import ComponentBase
import socket
import threading
import time
import sys
from vis_utils import constants

STANDARD_DT=1.0/120

def write_to_json_file(filename, serializable, indent=4):
    with open(filename, 'w') as outfile:
        print("save to ", filename)
        tmp = json.dumps(serializable, indent=4)
        outfile.write(tmp)
        outfile.close()

def to_unity_pc_frame(skeleton, frame, animated_joints, scale, action, events, is_idle=True, success=True):
    unity_frame = {"positions": [], "xAxisVectors": [], "yAxisVectors": [], "action": action, "isIdle": is_idle, "success": success}
    for index in range(len(animated_joints)):
        offset = index * 3
        p = frame[offset:offset + 3]
        unity_frame["positions"].append({"x": -p[0], "y": p[1], "z": p[2]})
    return unity_frame



def to_unity_frame(skeleton, frame, animated_joints, scale, action, events, is_idle=True, success=True):
    unity_frame = {"rotations": [], "rootTranslation": None, "action": action, "events": events, "isIdle": is_idle, "success": success}
    for node_name in skeleton.nodes.keys():
        if node_name in animated_joints:
            node = skeleton.nodes[node_name]
            if node_name == skeleton.root:
                t = frame[:3] * scale
                unity_frame["rootTranslation"] = {"x": -t[0], "y": t[1], "z": t[2]}

            if node_name in skeleton.animated_joints:  # use rotation from frame
                # TODO fix: the animated_joints is ordered differently than the nodes list for the latest model
                index = skeleton.animated_joints.index(node_name)
                offset = index * 4 + 3
                r = frame[offset:offset + 4]
                unity_frame["rotations"].append({"x": -r[1], "y": r[2], "z": r[3], "w": -r[0]})
            else:  # use fixed joint rotation
                r = node.rotation
                unity_frame["rotations"].append(
                    {"x": -float(r[1]), "y": float(r[2]), "z": float(r[3]), "w": -float(r[0])})
    return unity_frame


def to_unity_frame_all(skeleton, frame, animated_joints, scale, action, events, is_idle=True, success=True):
    unity_frame = {"rotations": [], "rootTranslation": None, "action": action, "events": events, "isIdle": is_idle, "success": success}
    for node_name in skeleton.nodes.keys():
        node = skeleton.nodes[node_name]
        r = node.rotation # set default rotation
        if len(node.children) > 0:
            if node_name == skeleton.root:
                t = frame[:3] * scale
                unity_frame["rootTranslation"] = {"x": -t[0], "y": t[1], "z": t[2]}
            if node_name in animated_joints:  # use rotation from frame
                # TODO fix: the animated_joints is ordered differently than the nodes list for the latest model
                index = animated_joints.index(node_name)
                offset = index * 4 + 3
                r = frame[offset:offset + 4]
                #unity_frame["rotations"].append({"x": -r[1], "y": r[2], "z": r[3], "w": -r[0]})
            #else:  # use fixed joint rotation
               
        unity_frame["rotations"].append({"x": -float(r[1]), "y": float(r[2]), "z": float(r[3]), "w": -float(r[0])})
    return unity_frame


def parse_message(input_bytes):
    """ decode byte into utf-8 string until 0x00 is found"""
    n_bytes = len(input_bytes)
    start_offset = 0
    end_offset = 0
    msg_str = ""
    while start_offset < n_bytes and start_offset < n_bytes:
        while end_offset < n_bytes and input_bytes[end_offset] != 0x00:
            end_offset += 1
        msg_str += bytes.decode(input_bytes[start_offset:end_offset], "utf-8")
        start_offset = end_offset + 1
    return msg_str


def parse_message2(input_bytes):
    """ decode byte into utf-8 string until end"""
    n_bytes = len(input_bytes)
    start_offset = 0
    end_offset = 0
    msg_str = ""
    while start_offset < n_bytes and end_offset < n_bytes:
        while end_offset < n_bytes:
            end_offset += 1

        print(bytes.decode(input_bytes[(start_offset + 1):(end_offset + 1)], "utf-8"))
        msg_str += bytes.decode(input_bytes[(start_offset + 1):(end_offset + 1)], "utf-8")
        end_offset += 1
        start_offset = end_offset
    return msg_str


def find_header_of_message(conn):
    LEN = 0
    data = b''
    header_received = False
    while not header_received:
        len_msg = conn.recv(1)
        data += len_msg
        if len(data) == 4:
            LEN = int.from_bytes(data, 'big')
            # print("Length: " + str(LEN))
            data = b''
            header_received = True

    while len(data) < LEN*2:
        byte = conn.recv(1)
        data += byte
    return data



def parse_client_message(server, client_msg_str):
    try:
        if client_msg_str.lower().startswith("ok"):
            return
        elif client_msg_str.startswith("Input:"):
            idx = len("Input:")
            input_key = client_msg_str[idx:idx + 1]
            server.input_key = input_key
        elif client_msg_str.startswith("Direction:"):
            idx = len("Direction:")
            #print("recieved", client_msg_str[idx:])
            vec = json.loads(client_msg_str[idx:])
            server.set_direction(np.array([vec["x"], vec["y"], vec["z"]]))
        elif client_msg_str.startswith("Action:"):
            idx = len("Action:")
            action = json.loads(client_msg_str[idx:])
            p = action["position"]
            if action["keyframe"] != "" and action["joint"] != "":
                position = np.array([p["x"], p["y"], p["z"]])
            else:
                position = None
            server.schedule_action(action, position)
        elif client_msg_str.startswith("SetPose:"):
            idx = len("SetPose:")
            print("setting pose", client_msg_str+"|")
            pose = json.loads(client_msg_str[idx:])
            p = pose["position"]
            q = pose["orientation"]
            server.set_avatar_orientation(np.array([q["w"],q["x"], q["y"], q["z"]]))
            server.set_avatar_position(np.array([p["x"], p["y"], p["z"]]))

        elif client_msg_str.startswith("ActionPath:"):
            #print("received", client_msg_str)
            idx = len("ActionPath:")
            action_desc = json.loads(client_msg_str[idx:])
            action_desc = convert_dicts_to_numpy(action_desc)
            server.schedule_action_path(action_desc)
        elif client_msg_str.startswith("ActionSequence:"):
            print("received", client_msg_str)
            idx = len("ActionSequence:")
            action_sequence_desc = json.loads(client_msg_str[idx:])
            _action_sequence_desc = []
            for action_desc in action_sequence_desc:
                action_desc = convert_dicts_to_numpy(action_desc)
                _action_sequence_desc.append(action_desc)
            server.schedule_action_sequence(_action_sequence_desc)
        elif client_msg_str.startswith("DirectionSequence:"):
            print("received", client_msg_str)
            idx = len("DirectionSequence:")
            dir_sequence_desc = json.loads(client_msg_str[idx:])
            _dir_sequence_desc = []
            for action_desc in dir_sequence_desc:
                action_desc = convert_dicts_to_numpy(action_desc)
                _dir_sequence_desc.append(action_desc)
            server.schedule_direction_sequence(_dir_sequence_desc)
        elif client_msg_str.startswith("SetScene:"):
            print("received", client_msg_str)
            idx = len("SetScene:")
            scene_desc = json.loads(client_msg_str[idx:])
            server.set_scene_from_desc(scene_desc)
            print("finished building scene")
        elif client_msg_str.startswith("Unpause"):
            server.unpause_motion()
        elif client_msg_str.startswith("PlayClip:"):
            idx = len("PlayClip:")
            action_desc = json.loads(client_msg_str[idx:])
            clip_name = action_desc["clip_name"]
            server.play_clip(clip_name)
        elif client_msg_str.startswith("HandleCollision"):
            server.handle_collision()
        else:
            print("Ignore message", client_msg_str)
    except Exception as e:
        print("Exception:",e.args)
        sys.exit(0)


def read_client_message_with_header(server, conn):
    input_bytes = conn.recv(server.buffer_size)
    while len(input_bytes) < 2:
        input_bytes += conn.recv(server.buffer_size)
    input_str = bytes.decode(input_bytes, "utf-8")
    if input_str[:2] == "m:":
        end_of_number = input_str[2:].find(':')
        message_size_str = input_str[2:2+end_of_number]
        message_size = int(message_size_str)
        message = input_str[2+end_of_number+1:]
        reached_end = False
        while len(message) < message_size and not reached_end:
            _input_bytes = conn.recv(server.buffer_size)
            n_bytes = len(_input_bytes)
            end_offset = 0
            while end_offset < n_bytes and _input_bytes[end_offset] != 0x00:
                end_offset += 1
            message += bytes.decode(_input_bytes[0:end_offset], "utf-8")
            reached_end = _input_bytes[end_offset-1] == 0x00
        parse_client_message(server, message.rstrip("\0"))# remove trailing null if present
        print(" reading", message)
    else:
        print("Error reading", input_str)


def receive_client_message(server, conn):
    if server.search_message_header:
        read_client_message_with_header(server, conn)
    else:
        input_bytes = conn.recv(server.buffer_size)
        client_msg_str = parse_message(input_bytes)
        parse_client_message(server, client_msg_str)

def convert_dicts_to_numpy(action_desc):
    for key in ["orientationVector", "lookAtTarget", "spineTarget","direction"]:
        if key in action_desc:
            v = action_desc[key]
            action_desc[key] = np.array([v["x"], v["y"], v["z"]])
    if "controlPoints" in action_desc:
        control_points = []
        for p in action_desc["controlPoints"]:
            control_points.append([p["x"], p["y"], p["z"]])
        action_desc["controlPoints"] = control_points
    if "frameConstraints" in action_desc:
        for c in action_desc["frameConstraints"]:
            p = c["position"]
            c["position"] = np.array([p["x"], p["y"], p["z"]])
            q = c["orientation"]
            c["orientation"] = np.array([q["w"], q["x"], q["y"], q["z"]])
            if "offset" in c:
                o = c["offset"]
                c["offset"] = np.array([o["x"], o["y"], o["z"], 1])
            if "vectorToParent" in c:
                v = c["vectorToParent"]
                c["vectorToParent"] = np.array([v["x"], v["y"], v["z"]])
            if "toolEndPoint" in c:
                o = c["toolEndPoint"]
                c["toolEndPoint"] = np.array([o["x"], o["y"], o["z"]])
            if "srcToolCos" in c:
                for a in ["x","y"]:
                    if a in c["srcToolCos"]:
                        o = c["srcToolCos"][a]
                        c["srcToolCos"][a] = np.array([o["x"], o["y"], o["z"]])
                        if np.linalg.norm(c["srcToolCos"][a]) <= 0:
                            del c["srcToolCos"][a]
            if "destToolCos" in c:
                for a in ["x","y"]:
                    if a in c["destToolCos"]:
                        o = c["destToolCos"][a]
                        c["destToolCos"][a] = np.array([o["x"], o["y"], o["z"]])
                        if np.linalg.norm(c["destToolCos"][a]) <= 0:
                            del c["destToolCos"][a]
    return action_desc

def send_message(server, conn, msg):
    if server.search_message_header:
        msg = "m:" + str(len(msg)) + ":" + msg
    msg = msg.encode("utf-8")
    msg += b'\x00'
    conn.sendall(msg)

def on_new_client(server, conn, addr):
    #client_msg = conn.recv(1024)
    print("welcome",addr)
    receive_client_message(server, conn)
    skel_dict = server.get_skeleton_dict()
    server_msg = json.dumps(skel_dict)
    #print("send", len(server_msg), server_msg)
    send_message(server, conn, server_msg)
    print("wait for initial answer")
    #client_msg = conn.recv(server.buffer_size)
    receive_client_message(server, conn)
    print("received answer")
    while True:
        try:
            frame = server.get_frame()
            if frame is not None:
                server_msg = json.dumps(frame)
            else:
                server_msg = ""
            send_message(server, conn, server_msg)
            time.sleep(server.get_frame_time())
            receive_client_message(server, conn)

        except socket.error as error:
            print("connection was closed", error.args)
            server.set_direction(np.array([0,0,0]))
            conn.close()
            return
    conn.close()


def server_thread(server, s):
    print("server started")
    while server.run:
        c, addr = s.accept()
        t = threading.Thread(target=on_new_client, name="addr", args=(server, c, addr))
        t.start()
        server.connections[addr] = t
    print("server stopped")
    s.close()


class TCPServer(object):
    """ TCP server that sends and receives a single message
        https://pymotw.com/2/socket/tcp.html
    """
    BUFFER_SIZE = 4092*10000#10485760

    def __init__(self, port, buffer_size=BUFFER_SIZE):
        self.address = ("", port)
        self.buffer_size = buffer_size
        self.connections = dict()
        self.run = True
        self.input_key = ""

    def start(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(self.address)
        except socket.error:
            print("Binding failed")
            return

        s.listen(10)
        t = threading.Thread(target=server_thread, name="c", args=(self, s))
        t.start()
        print("started server")

    def close(self):
        self.run = False

    def get_frame(self):
        return b"frame\n"

