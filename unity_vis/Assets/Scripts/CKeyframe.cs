using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CustomAnimation
{

        [System.Serializable]
    public class StartPose
    {
        public Vector3 position;
        public Quaternion orientation;
        public bool forceWalkEndConstraints;
    }

    [System.Serializable]
    public class CKeyframe{
        
		public Vector4[] rotations;      
        public Vector3[] positions;
    }

    
}
