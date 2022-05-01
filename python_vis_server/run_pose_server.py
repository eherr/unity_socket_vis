
from anim_utils.animation_data import BVHReader, SkeletonBuilder, MotionVector
from vis_utils.console_app import ConsoleApp
from vis_utils.glut_app import GLUTApp
from pose_server_component import PoseServerComponent
from vis_utils.animation.skeleton_animation_controller import SkeletonAnimationController
from vis_utils.scene.scene_object import SceneObject
from vis_utils.scene.utils import get_random_color


def handle_keys(key, data):
    app, controller = data
    if key== b" ":
        controller._motion.play = not controller._motion.play

def load_skeleton(filename):
    bvhreader = BVHReader(filename)
    skeleton = SkeletonBuilder().load_from_bvh(bvhreader)
    return skeleton

def load_mv(filename):
    bvh = BVHReader(filename)
    mv = MotionVector()
    mv.from_bvh_reader(bvh, False)
    return mv

def create_skeleton_animation_controller(builder, skeleton, motion_vector, frame_time, draw_mode=2, visualize=True, color=None, ):
    scene_object = SceneObject()
    animation_controller = SkeletonAnimationController(scene_object)
    animation_controller.set_motion(motion_vector)
    animation_controller.frameTime = frame_time
    scene_object.name = animation_controller.name
    scene_object.add_component("animation_controller", animation_controller)
    vis = None
    if visualize:
        if color is None:
            color = get_random_color()
        vis = builder.create_component("skeleton_vis", scene_object, skeleton, color=color)
        animation_controller.set_visualization(vis, draw_mode)
        builder._scene.addAnimationController(scene_object, "animation_controller")
    else:
        animation_controller.set_skeleton(skeleton)
        builder._scene.addObject(scene_object)
    return scene_object



def setup_scene(app, skeleton_file, data_file, port, visualize=False):
    scene = app.scene
    skeleton = load_skeleton(skeleton_file)
    mv = load_mv(data_file)
    print(mv.frame_time)

    o = create_skeleton_animation_controller(scene.object_builder, skeleton, mv, mv.frame_time, visualize=visualize)
    animation_controller = o._components["animation_controller"]
    animation_controller._motion.play = True
    animation_controller.loopAnimation = True
    src = "animation_controller"
    o.add_component(src, animation_controller)

    server = PoseServerComponent(port, o, src)
    o.add_component("pose_server", server)
    if visualize:
        scene.addAnimationController(o, src)
        app.set_camera_target(o)
    else:
        scene.addObject(o)
    data = app, animation_controller
    app.keyboard_handler["i"] = handle_keys, data
    server.start()
    
    return o

def main():
    app_fps = 200
    sim_settings = None
    sync_sim = False
    sim_dt = 1/30.0
    port = 8888
    visualize = False
    skeleton_file = r"data/merengue.bvh"
    data_file = r"data/merengue.bvh"
    if visualize:
        a = GLUTApp(800, 600, title="GLUTApp", camera_pose=None, maxfps=app_fps, sim_settings=sim_settings, sync_sim=sync_sim, sim_dt=sim_dt)
    else:
        a = ConsoleApp(fps=app_fps, sim_settings=sim_settings, sync_sim=sync_sim, sim_dt=sim_dt)
    o = setup_scene(a, skeleton_file, data_file, port, visualize)
    
    try:
        a.run()
    except KeyboardInterrupt:
        print("Shutdown")



if __name__ == "__main__":
    main()

