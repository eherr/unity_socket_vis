using UnityEngine;

namespace CustomAnimation
{
	[System.Serializable]
	public class SkeletonDesc
	{
		public string root;
		public JointDesc[] jointDescs;
		public string[] jointSequence;
	}



}
