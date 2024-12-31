using UnityEngine;
using TMPro; // Use TextMeshPro namespace

public class Timer : MonoBehaviour
{
    public float timerDuration = 90f; // 1 minute and 30 seconds in seconds
    private float timeRemaining;
    private bool timerIsRunning = false;

    public TextMeshProUGUI timerText; // Drag the TextMeshPro object here to display the timer
    public TextMeshProUGUI resultText; // Drag the TextMeshPro object here to display "You Won!" or "Time's Up!"
    public int snapCount = 0; // Track the number of snapped objects

    void Start()
    {
        timeRemaining = timerDuration;
        timerIsRunning = true; // Start the timer
        if (resultText != null)
        {
            resultText.text = ""; // Clear any previous message
        }
    }

    void Update()
    {
        if (timerIsRunning)
        {
            if (timeRemaining > 0)
            {
                timeRemaining -= Time.deltaTime; // Reduce time
                DisplayTime(timeRemaining);     // Update timer display

                // Check if snapCount == 7
                if (snapCount == 7)
                {
                    TimerWon();
                }
            }
            else
            {
                timeRemaining = 0;
                timerIsRunning = false;
                TimerLost();
            }
        }
    }

    void DisplayTime(float timeToDisplay)
    {
        if (timerText != null)
        {
            timeToDisplay = Mathf.Max(0, timeToDisplay); // Prevent negative time display
            int minutes = Mathf.FloorToInt(timeToDisplay / 60);
            int seconds = Mathf.FloorToInt(timeToDisplay % 60);
            timerText.text = string.Format("{0:00}:{1:00}", minutes, seconds);
        }
    }

    void TimerWon()
    {
        timerIsRunning = false; // Stop the timer
        if (resultText != null)
        {
            resultText.text = "You Won!";
        }
        Debug.Log("You Won!"); // Debug message
    }

    void TimerLost()
    {
        if (resultText != null)
        {
            resultText.text = "Time's Up!";
        }
        Debug.Log("Time's Up!"); // Debug message
    }

    // Method to increment snapCount (call this from your snapping logic)
    public void IncrementSnapCount()
    {
        snapCount++;
    }
}
