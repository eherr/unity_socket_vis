using System;
using System.Collections.Generic;
using UnityEngine;
using CustomAnimation;

public abstract class NetworkPoseProvider : MonoBehaviour {

    public float scaleFactor;
    public CKeyframe pose;
    protected Dictionary<string, int> indexMap;
    public bool Initialized {get => pose != null;}
    virtual public Quaternion GetGlobalRotation(string srcJoint)
    {
        int boneIdx = indexMap[srcJoint];
        var v = pose.rotations[boneIdx];
        var q = new Quaternion(v[0], v[1], v[2], v[3]);
        return q;
    }

    virtual public Vector3 GetGlobalPosition(string srcJoint)
    {
        int boneIdx = indexMap[srcJoint];
        var v = pose.positions[boneIdx]*scaleFactor;
        return new Vector3(v[0], v[1], v[2]);
    }

    virtual public bool GetGlobalPosition(string srcJoint, out Vector3 p)
    {
        p = new Vector3();
        if (pose == null) return false;
       int boneIdx = indexMap[srcJoint];
        var v = pose.positions[boneIdx]*scaleFactor;
        p =  new Vector3(v[0], v[1], v[2]);
        return true;
    }

    virtual public bool GetGlobalRotation(string srcJoint, out Quaternion q)
    {
        q = new Quaternion();
        if (pose == null) return false;
        int boneIdx = indexMap[srcJoint];
        var v = pose.rotations[boneIdx];
        q = new Quaternion(v[0], v[1], v[2], v[3]);
        return true;
    }

};