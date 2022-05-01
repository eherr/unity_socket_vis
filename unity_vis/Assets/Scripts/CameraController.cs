//author: Erik Herrmann
//orbiting camera based on http://www.glprogramming.com/red/chapter03.html and https://forum.unity.com/threads/how-to-change-main-camera-pivot.700442/
//Horizontal movement based on
//http://www.youtube.com/watch?v=RInkwoCgIps
//http://www.youtube.com/watch?v=H20stuPG-To

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CameraController : MonoBehaviour
{

    Vector3 lastPos;
    Vector3 delta;
    Camera cam;
    public float rotationScale = 1f;
    public float translationScale = 0.1f;
    public float zoomSpeed = 1f;
    bool isRotating;
    bool isTranslating;
    public float FPS = 60;
    float syncTimer = 0;

    public float pitch = 0;
    public float yaw = 0;
    public float zoom = 0;
    public bool Active;
    public Transform cameraTransform;
    public Transform cameraTarget;
    const int ROTATE_BUTTON = 0;//1;
    const int TRANSLATE_BUTTON = 1;//2;
    void Start()
    {
        isRotating = false;
        isTranslating = false;
        //set initial values from transform
        yaw = cameraTarget.eulerAngles.y;
        // pitch = cameraTarget.eulerAngles.x;
        syncTimer = 1.0f / 60;
        rotate(Vector2.zero, 0);

    }

    void Update()
    {
        float interval = 1.0f / FPS;
        if (syncTimer > interval)
        {
            syncTimer -= Time.deltaTime;
            return;
        }
        if (Active) { 
            //handleTranslationInput();

            handleZoomInput(interval);
            handleRotationInput(interval);
        }

        cameraTransform.localPosition = new Vector3(0, 0, zoom);
        var qx = Quaternion.Euler(pitch, 0, 0);
        var qy = Quaternion.Euler(0, yaw, 0);
        cameraTarget.rotation = qy * qx;
    }

    void handleZoomInput(float dt)
    {

        if (!isTranslating)
        {
            zoom += dt*Input.mouseScrollDelta.y * zoomSpeed;
            //cameraTransform.Translate(0, 0, z * zoomSpeed, Space.Self);
        }
    }

    void handleTranslationInput(float dt)
    {

        if (Input.GetMouseButtonDown(TRANSLATE_BUTTON))
        {
            if (!isRotating)
            {
                lastPos = Input.mousePosition;
                delta = Vector3.zero;

                isTranslating = true;
            }
        }
        if (Input.GetMouseButtonUp(TRANSLATE_BUTTON))
        {
            isTranslating = false;
        }
        if (isTranslating)
        {
            delta = Input.mousePosition - lastPos;
            translate(delta, dt);
            lastPos = Input.mousePosition;
        }
    }

    void handleRotationInput(float dt)
    {
        if (Input.GetMouseButtonDown(ROTATE_BUTTON))
        {
            if (!isRotating)
            {
                lastPos = Input.mousePosition;
                delta = Vector3.zero;
                isRotating = true;
            }
        }
        if (Input.GetMouseButtonUp(ROTATE_BUTTON))
        {
            isRotating = false;
        }
        if (isRotating)
        {
            delta = Input.mousePosition - lastPos;
            rotate(delta, dt);
            lastPos = Input.mousePosition;
        }
    }

    void rotate(Vector2 delta, float dt)
    {

        yaw += rotationScale * dt *  delta.x;
        pitch += rotationScale * dt * -delta.y;


        yaw %= 360;
        pitch %= 360;
    }

    public Vector2 PredictRotation(float dt)
    {
        float x = pitch + rotationScale * dt * -delta.y;
        float y = yaw + rotationScale * dt * delta.x;
        return new Vector2(x % 360, y % 360);
    }

    void translate(Vector2 delta, float dt)
    {
        var pos = cameraTarget.position;
        var rad = Mathf.Deg2Rad * -yaw;
        float distance = dt * -delta.x * translationScale * 2;
        pos.x += distance * Mathf.Cos(rad);
        pos.z += distance * Mathf.Sin(rad);
        pos.y -= translationScale * delta.y;
        cameraTarget.position = pos;

    }

}
