using UnityEngine;

public class SnapToTargetPosition3D : MonoBehaviour
{
    public Transform targetPosition;  // The target position for this piece to snap to
    public float snapRange = 1.0f;    // Distance within which snapping occurs (adjust for 3D space)
    private bool isSnapped = false;   // Tracks if this object is snapped to the target
    private Vector3 offset;           // To store the drag offset
    private Camera mainCamera;        // Reference to the main camera

    void Start()
    {
        mainCamera = Camera.main;  // Get the main camera reference
    }

    void Update()
    {
        // If not snapped, allow dragging and snapping
        if (!isSnapped)
        {
            TrySnapToTarget();
        }
    }

    private void TrySnapToTarget()
    {
        // Check if the piece is within range of the target
        float distance = Vector3.Distance(transform.position, targetPosition.position);

        // Snap to target and lock movement if within range
        if (distance <= snapRange)
        {
            SnapToTarget();
        }
    }

    private void SnapToTarget()
    {
        // Move the piece to the target position
        transform.position = targetPosition.position;

        // Mark as snapped to prevent further dragging
        isSnapped = true;
    }

    void OnMouseDown()
    {
        // Only calculate offset if not yet snapped
        if (!isSnapped)
        {
            offset = transform.position - GetMouseWorldPosition();
        }
    }

    void OnMouseDrag()
    {
        // Only allow dragging if not yet snapped
        if (!isSnapped)
        {
            transform.position = GetMouseWorldPosition() + offset;
        }
    }

    private Vector3 GetMouseWorldPosition()
    {
        // Convert mouse position to world position (for 3D space)
        Vector3 mousePoint = Input.mousePosition;
        mousePoint.z = mainCamera.WorldToScreenPoint(transform.position).z;
        return mainCamera.ScreenToWorldPoint(mousePoint);
    }
}
