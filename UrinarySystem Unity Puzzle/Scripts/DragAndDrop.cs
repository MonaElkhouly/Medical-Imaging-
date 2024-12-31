using UnityEngine;

public class DragObject : MonoBehaviour
{
    private Vector3 offset;
    private float zCoord;
    public Camera mainCamera;
    public bool isDraggable = true;
    public bool isDragging = false;
    public float dragSpeed = 1f; // Adjust drag speed in inspector if needed

    public SnapToTargetPosition3D snapScript;
    public Rigidbody rb;

    void Start()
    {
        mainCamera = Camera.main;
        snapScript = GetComponent<SnapToTargetPosition3D>();
        rb = GetComponent<Rigidbody>();

        // Add Rigidbody if it doesn't exist
        if (rb == null)
        {
            rb = gameObject.AddComponent<Rigidbody>();
            rb.useGravity = false;
            rb.isKinematic = true;
        }
    }

    void OnMouseDown()
    {
        if (!isDraggable || (snapScript != null && snapScript.isSnapped))
            return;

        isDragging = true;
        zCoord = mainCamera.WorldToScreenPoint(transform.position).z;
        offset = transform.position - GetMouseWorldPos();
    }

    void OnMouseDrag()
    {
        if (!isDraggable || !isDragging || (snapScript != null && snapScript.isSnapped))
            return;

        Vector3 targetPosition = GetMouseWorldPos() + offset;
        Vector3 smoothPosition = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * dragSpeed * 10f);
        transform.position = smoothPosition;
    }

    void OnMouseUp()
    {
        isDragging = false;
    }

    private Vector3 GetMouseWorldPos()
    {
        Vector3 mousePoint = Input.mousePosition;
        mousePoint.z = zCoord;
        return mainCamera.ScreenToWorldPoint(mousePoint);
    }

    public void ResetTransform()
    {
        if (snapScript != null && !snapScript.isSnapped)
        {
            isDragging = false;
            transform.position = Vector3.zero; // Or any default position
        }
    }
}