import numpy as np
from vis_utils.scene.components import ComponentBase
import socket
import threading
from vis_utils import constants
from tcp_server import TCPServer, server_thread
from transformations import quaternion_from_matrix

STANDARD_DT=1.0/120


def to_unity_pose(skeleton, frame, animated_joints, scale):
    unity_frame = {"rotations": [], "positions": []}
    skeleton.clear_cached_global_matrices()
    for node_name in animated_joints:
        matrix = skeleton.nodes[node_name].get_global_matrix(frame, True)
        p = matrix[:3, 3] * scale
        unity_frame["positions"].append({"x": -p[0], "y": p[1], "z": p[2]})
        q = quaternion_from_matrix(matrix)
        unity_frame["rotations"].append({"x": -q[1], "y": q[2], "z": q[3], "w": -q[0]})
      
    return unity_frame


class PoseServerComponent(ComponentBase, TCPServer):
    def __init__(self, port, scene_object, src_component):
        print("create animation server", port)
        ComponentBase.__init__(self, scene_object)
        TCPServer.__init__(self, port)
        self.src_component_key = src_component
        self.animation_src = scene_object._components[src_component]
        self.animation_src.animation_server = self
        self.activate_emit = True
        self.frame_buffer = None
        self.skeleton = self.animation_src.get_skeleton()
        self.animated_joints = [key for key in self.skeleton.nodes.keys() if len(self.skeleton.nodes[key].children) >0]
        self.scale = 100.0
        self.search_message_header = False
        self.activate_simulation = constants.activate_simulation

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

    def update(self, dt):
        frame = self.animation_src.get_current_frame()
        if frame is None:
            return
        self.frame_buffer = to_unity_pose(self.skeleton, frame, self.animated_joints, self.scale)
        

    def get_frame(self):
        return self.frame_buffer

    def get_frame_time(self):
        return self.animation_src.get_frame_time()

    def get_skeleton_dict(self):
        desc = self.skeleton.to_unity_format(animated_joints=self.animated_joints)
        #print(self.animated_joints, desc["jointDescs"])
        return desc

    def set_direction(self, direction_vector):
        if self.src_component_key == "pfnn_wrapper":
            length = np.linalg.norm(direction_vector)
            if length > 0:
                self.animation_src.direction_vector = direction_vector/length
                self.animation_src.target_projection_len = length
            else:
                self.animation_src.target_projection_len = 0

    def set_avatar_position(self, position):
        print("set position", position)
        if self.src_component_key == "morphablegraph_state_machine":
            self.animation_src.set_global_position(position)

    def set_avatar_orientation(self, orientation):
        print("set orientation", orientation)
        if self.src_component_key == "morphablegraph_state_machine":
            self.animation_src.set_global_orientation(orientation)