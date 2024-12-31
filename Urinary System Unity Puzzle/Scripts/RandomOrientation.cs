using UnityEngine;

public class RandomizePositionAtStart : MonoBehaviour
{
    // Define the range for randomizing position
    public Vector3 positionOffset = new Vector3(100f, 100f, 100f);

    // Whether to randomize orientation
    public bool randomizeRotation = true;
    public Vector3 rotationRange = new Vector3(90f, 0f, 0f); // Rotation range for X, Y, Z axes

    void Start()
    {
        foreach (Transform child in transform)
        {
            // Preserve the original scale
            Vector3 originalScale = child.localScale;

            // Randomize position within the specified range
            float randomX = Random.Range(-positionOffset.x, positionOffset.x);
            float randomY = Random.Range(-positionOffset.y, positionOffset.y);
            float randomZ = Random.Range(-positionOffset.z, positionOffset.z);
            child.localPosition = new Vector3(randomX, randomY, randomZ);

            // Randomize rotation if enabled
            if (randomizeRotation)
            {
                float randomRotX = Random.Range(-rotationRange.x, rotationRange.x);
                float randomRotY = Random.Range(-rotationRange.y, rotationRange.y);
                float randomRotZ = Random.Range(-rotationRange.z, rotationRange.z);
                child.localRotation = Quaternion.Euler(randomRotX, randomRotY, randomRotZ);
            }

            // Restore the original scale
            child.localScale = originalScale;
        }
    }
}
