import numpy as np
from vis_utils.scene.components import ComponentBase
import socket
import threading
from vis_utils import constants
from animation_tcp_server import AnimationTCPServer
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


class PoseServerComponent(ComponentBase):
    def __init__(self, port, scene_object, src_component):
        print("create animation server", port)
        ComponentBase.__init__(self, scene_object)
        self.server = AnimationTCPServer(port, self)
        self.animation_src = scene_object._components[src_component]
        self.animation_src.animation_server = self
        self.activate_emit = True
        self.frame_buffer = None
        self.skeleton = self.animation_src.get_skeleton()
        self.animated_joints = [key for key in self.skeleton.nodes.keys() if len(self.skeleton.nodes[key].children) >0]
        self.scale = 100.0
        self.activate_simulation = constants.activate_simulation
        self.skeleton_dict = self.skeleton.to_unity_format(animated_joints=self.animated_joints)

    def start(self):
        self.server.start()

    def update(self, dt):
        frame = self.animation_src.get_current_frame()
        if frame is None:
            return
        self.frame_buffer = to_unity_pose(self.skeleton, frame, self.animated_joints, self.scale)

    @property
    def frame_time(self):
        return self.animation_src.get_frame_time()
