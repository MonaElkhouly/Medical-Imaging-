
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
from ultralytics import YOLO
from scipy.ndimage import gaussian_filter


@dataclass
class VideoState:
    path: str = ""
    cap: Optional[cv2.VideoCapture] = None
    is_playing: bool = False
    is_paused: bool = False
    frame_count: int = 0
    current_frame: int = 0
    fps: float = 0.0


class FootballTrackerGUI:
    def __init__(self):
        # Initialize states
        self.video_state = VideoState()
        self.model = YOLO('yolov8n.pt')
        self.player_positions: Dict[int, list] = {}
        self.selected_player_id: Optional[int] = None
        self.last_positions = {}  # Store last known positions
        self.next_id = 1  # For assigning new IDs

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        """Initialize the main GUI window and theme"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Football Player Tracker Pro")
        self.root.geometry("1400x800")

        # Create main containers
        self.create_left_panel()
        self.create_right_panel()

    def create_left_panel(self):
        """Create the control panel on the left side"""
        left_panel = ctk.CTkFrame(self.root, width=300)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)

        # Title Section
        self._create_title_section(left_panel)

        # Video Controls Section
        self._create_video_controls(left_panel)

        # Player Tracking Section
        self._create_tracking_section(left_panel)

        # Statistics Section
        self._create_stats_section(left_panel)

    def _create_title_section(self, parent):
        """Create the title section"""
        title = ctk.CTkLabel(
            parent,
            text="Football Player Tracker",
            font=("Helvetica", 22, "bold")
        )
        title.pack(pady=20)

    def _create_video_controls(self, parent):
        """Create video control buttons and displays"""
        video_frame = ctk.CTkFrame(parent)
        video_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(video_frame, text="Video Controls",
                     font=("Helvetica", 16, "bold")).pack(pady=10)

        # Upload button
        self.upload_btn = ctk.CTkButton(
            video_frame,
            text="Upload Video",
            command=self.upload_video,
            height=40,
            font=("Helvetica", 13)
        )
        self.upload_btn.pack(pady=5, fill="x")

        # Video info display
        self.video_info = ctk.CTkLabel(
            video_frame,
            text="No video selected",
            wraplength=250
        )
        self.video_info.pack(pady=5)

        # Playback controls
        self._create_playback_controls(video_frame)

        # Add progress bar
        self._create_progress_bar(video_frame)

    def _create_playback_controls(self, parent):
        """Create play/pause buttons"""
        controls = ctk.CTkFrame(parent)
        controls.pack(fill="x", pady=10)

        self.play_btn = ctk.CTkButton(
            controls,
            text="▶ Play",
            command=self.play_video,
            width=90,
            state="disabled"
        )
        self.play_btn.pack(side="left", padx=5)

        self.pause_btn = ctk.CTkButton(
            controls,
            text="⏸ Pause",
            command=self.pause_video,
            width=90,
            state="disabled"
        )
        self.pause_btn.pack(side="right", padx=5)

    def _create_tracking_section(self, parent):
        """Create the player tracking controls section"""
        tracking_frame = ctk.CTkFrame(parent)
        tracking_frame.pack(fill="x", padx=10, pady=10)

        # Section title
        ctk.CTkLabel(tracking_frame, text="Player Tracking",
                     font=("Helvetica", 16, "bold")).pack(pady=10)

        # Player selection
        self.player_dropdown = ctk.CTkComboBox(
            tracking_frame,
            values=["No players detected"],
            command=self._on_player_selected,
            state="disabled",
            variable=tk.StringVar(value="Select Player")
        )
        self.player_dropdown.pack(pady=5, fill="x")

        # Tracking controls
        controls = ctk.CTkFrame(tracking_frame)
        controls.pack(fill="x", pady=5)

        self.track_btn = ctk.CTkButton(
            controls,
            text="Start Tracking",
            command=self._toggle_tracking,
            state="disabled",
            width=90
        )
        self.track_btn.pack(side="left", padx=5)

        self.clear_btn = ctk.CTkButton(
            controls,
            text="Clear Data",
            command=self._clear_tracking,
            state="disabled",
            width=90
        )
        self.clear_btn.pack(side="right", padx=5)

        # Position display
        self.position_label = ctk.CTkLabel(
            tracking_frame,
            text="Position: --",
            font=("Helvetica", 12)
        )
        self.position_label.pack(pady=5)

    def _create_stats_section(self, parent):
        """Create the data display section for selected player"""
        data_frame = ctk.CTkFrame(parent)
        data_frame.pack(fill="x", padx=10, pady=10)

        # Section title
        ctk.CTkLabel(data_frame,
                     text="Data of Selected Player",
                     font=("Helvetica", 16, "bold")).pack(pady=10)

        # Data display with larger font
        self.stats_text = ctk.CTkTextbox(
            data_frame,
            height=150,
            font=("Helvetica", 14),
            state="disabled"
        )
        self.stats_text.pack(pady=5, fill="x")

        # Export button
        self.export_btn = ctk.CTkButton(
            data_frame,
            text="Export Data",
            command=self._export_data,
            state="disabled"
        )
        self.export_btn.pack(pady=5, fill="x")

    def _create_progress_bar(self, parent):
        """Create progress bar for video playback"""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        self.time_label = ctk.CTkLabel(progress_frame, text="00:00 / 00:00")
        self.time_label.pack(pady=2)

    def create_right_panel(self):
        """Create the visualization panel on the right side"""
        self.right_panel = ctk.CTkFrame(self.root)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Create video container with title
        video_container = ctk.CTkFrame(self.right_panel)
        video_container.pack(fill="both", expand=True, pady=5)

        # Add title for video
        ctk.CTkLabel(video_container,
                     text="Video View",
                     font=("Helvetica", 14, "bold")).pack(pady=5)

        # Create video frame with GUI theme color
        video_bg = ctk.CTkFrame(video_container)  # Using default CTkFrame color
        video_bg.pack(fill="both", expand=True)

        # Create video display label with matching background
        self.video_display = tk.Label(video_bg, bg='#2b2b2b')  # Dark theme color
        self.video_display.pack(fill="both", expand=True)

        # Create pitch visualization
        self.create_pitch_visualization()

    def create_pitch_visualization(self):
        """Create 2D football pitch visualization"""
        self.pitch_frame = ctk.CTkFrame(self.right_panel)
        self.pitch_frame.pack(fill="both", expand=True, pady=10)

        # Create a frame to hold both pitches horizontally
        pitches_frame = ctk.CTkFrame(self.pitch_frame)
        pitches_frame.pack(fill="both", expand=True)

        # Create left pitch container with title
        left_container = ctk.CTkFrame(pitches_frame)
        left_container.pack(side="left", fill="both", expand=True, padx=5)

        # Add title for left pitch
        ctk.CTkLabel(left_container,
                     text="Heatmap",
                     font=("Helvetica", 14, "bold")).pack(pady=5)

        # Create left pitch
        self.pitch_canvas_left = tk.Canvas(
            left_container,
            bg='dark green',
            highlightthickness=0
        )
        self.pitch_canvas_left.pack(fill="both", expand=True)

        # Create right pitch container with title
        right_container = ctk.CTkFrame(pitches_frame)
        right_container.pack(side="right", fill="both", expand=True, padx=5)

        # Add title for right pitch
        ctk.CTkLabel(right_container,
                     text="2D Plane",
                     font=("Helvetica", 14, "bold")).pack(pady=5)

        # Create right pitch
        self.pitch_canvas_right = tk.Canvas(
            right_container,
            bg='dark green',
            highlightthickness=0
        )
        self.pitch_canvas_right.pack(fill="both", expand=True)

        # Bind resize event to update pitch lines
        self.pitch_canvas_left.bind('<Configure>', lambda e: self._draw_pitch_lines(self.pitch_canvas_left))
        self.pitch_canvas_right.bind('<Configure>', lambda e: self._draw_pitch_lines(self.pitch_canvas_right))

    def _draw_pitch_lines(self, canvas):
        """Draw the football pitch markings"""
        # Get current canvas dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        # Clear previous drawings
        canvas.delete("all")

        # Calculate margins (10% of dimensions)
        margin_x = width * 0.1
        margin_y = height * 0.1

        # Calculate usable area
        field_width = width - (2 * margin_x)
        field_height = height - (2 * margin_y)

        # Field outline
        canvas.create_rectangle(
            margin_x, margin_y,
            width - margin_x, height - margin_y,
            outline='white', width=2
        )

        # Center line
        center_x = width / 2
        canvas.create_line(
            center_x, margin_y,
            center_x, height - margin_y,
            fill='white', width=2
        )

        # Center circle
        circle_radius = min(field_width, field_height) * 0.15
        canvas.create_oval(
            center_x - circle_radius, (height / 2) - circle_radius,
            center_x + circle_radius, (height / 2) + circle_radius,
            outline='white', width=2
        )

        # Penalty areas
        penalty_width = field_width * 0.2
        penalty_height = field_height * 0.5
        penalty_y_start = (height - penalty_height) / 2

        # Left penalty area
        canvas.create_rectangle(
            margin_x, penalty_y_start,
            margin_x + penalty_width, penalty_y_start + penalty_height,
            outline='white', width=2
        )

        # Right penalty area
        canvas.create_rectangle(
            width - margin_x - penalty_width, penalty_y_start,
            width - margin_x, penalty_y_start + penalty_height,
            outline='white', width=2
        )

    def upload_video(self):
        """Handle video file selection and loading"""
        try:
            video_path = filedialog.askopenfilename(
                title="Select Football Video",
                filetypes=[
                    ("Video Files", "*.mp4 *.avi *.mov *.mkv"),
                    ("All Files", "*.*")
                ]
            )

            if video_path:
                self._load_video(video_path)

        except Exception as e:
            self._handle_error(f"Error uploading video: {str(e)}")

    def _load_video(self, path: str):
        """Load and initialize video file"""
        try:
            # Release previous capture if exists
            if self.video_state.cap is not None:
                self.video_state.cap.release()

            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                raise Exception("Failed to open video file")

            # Update video state
            self.video_state = VideoState(
                path=path,
                cap=cap,
                frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                fps=cap.get(cv2.CAP_PROP_FPS)
            )

            # Display first frame
            self._display_frame()

            # Update UI
            self._update_video_info()
            self.play_btn.configure(state="normal")

        except Exception as e:
            self._handle_error(f"Error loading video: {str(e)}")

    def _display_frame(self):
        """Display current video frame"""
        if self.video_state.cap is None:
            return

        ret, frame = self.video_state.cap.read()
        if ret:
            frame = cv2.resize(frame, (800, 600))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            self.video_display.configure(image=img_tk)
            self.video_display.image = img_tk

    def _update_video_info(self):
        """Update video information display"""
        filename = os.path.basename(self.video_state.path)
        info = f"Video: {filename}\n"
        info += f"Frames: {self.video_state.frame_count}\n"
        info += f"FPS: {self.video_state.fps:.2f}"
        self.video_info.configure(text=info)

    def _handle_error(self, message: str):
        """Handle and display errors"""
        print(f"Error: {message}")
        messagebox.showerror("Error", message)

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

    def _update_frame(self):
        """Update video frame and tracking data"""
        if self.video_state.is_playing and not self.video_state.is_paused:
            try:
                ret, frame = self.video_state.cap.read()
                if ret:
                    # Update progress less frequently
                    if self.video_state.current_frame % 3 == 0:  # Update every 3 frames
                        current_frame = self.video_state.cap.get(cv2.CAP_PROP_POS_FRAMES)
                        progress = current_frame / self.video_state.frame_count
                        self.progress_bar.set(progress)

                        # Update time display
                        current_time = current_frame / self.video_state.fps
                        total_time = self.video_state.frame_count / self.video_state.fps
                        self.time_label.configure(
                            text=f"{self._format_time(current_time)} / {self._format_time(total_time)}"
                        )

                    # Process frame with YOLO tracking
                    self.update_player_tracking(frame)

                    # Increment frame counter
                    self.video_state.current_frame += 1

                    # Calculate delay to maintain correct FPS
                    delay = int(1000 / self.video_state.fps)
                    self.root.after(delay, self._update_frame)
                else:
                    # Video ended
                    self.video_state.is_playing = False
                    self.play_btn.configure(state="normal")
                    self.pause_btn.configure(state="disabled")
                    # Reset video to start
                    self.video_state.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.video_state.current_frame = 0

            except Exception as e:
                print(f"Frame update error: {str(e)}")
                self.video_state.is_playing = False
                self.play_btn.configure(state="normal")
                self.pause_btn.configure(state="disabled")

    def play_video(self):
        """Handle video playback"""
        if not self.video_state.is_playing:
            self.video_state.is_playing = True
            self.video_state.is_paused = False
            self.play_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal", text="⏸ Pause")
            self._update_frame()

    def pause_video(self):
        """Handle video pause"""
        if self.video_state.cap is None:
            return

        self.video_state.is_paused = not self.video_state.is_paused
        if self.video_state.is_paused:
            self.pause_btn.configure(text="Resume")
            self.play_btn.configure(state="normal")
        else:
            self.pause_btn.configure(text="Pause")
            self.play_btn.configure(state="disabled")
            self._update_frame()

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _export_data(self):
        """Export tracking data to CSV"""
        if not self.player_positions:
            messagebox.showwarning("Warning", "No tracking data to export")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                import csv
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Player ID", "Frame", "X", "Y"])
                    for player_id, positions in self.player_positions.items():
                        for frame, (x, y) in enumerate(positions):
                            writer.writerow([player_id, frame, x, y])
                messagebox.showinfo("Success", "Data exported successfully")
        except Exception as e:
            self._handle_error(f"Error exporting data: {str(e)}")

    def _on_player_selected(self, choice):
        """Handle player selection from dropdown"""
        try:
            player_id = int(choice.split()[1])  # Extract ID from "Player X"
            self.selected_player_id = player_id
            self.track_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")

            # Reset tracking state when new player is selected
            self.is_tracking_stats = False
            self.track_btn.configure(text="Start Tracking")

            # Clear previous stats
            self.stats_text.configure(state="normal")
            self.stats_text.delete("1.0", tk.END)
            self.stats_text.configure(state="disabled")

        except:
            self.selected_player_id = None
            self.track_btn.configure(state="disabled")
            self.clear_btn.configure(state="disabled")

    def _toggle_tracking(self):
        """Toggle player tracking on/off"""
        if self.selected_player_id is None:
            return

        is_tracking = self.track_btn.cget("text") == "Stop Tracking"
        if is_tracking:
            self.track_btn.configure(text="Start Tracking")
            self.is_tracking_2d = False
            # Clear 2D tracking
            self.pitch_canvas_right.delete("movement")
        else:
            self.track_btn.configure(text="Stop Tracking")
            self.is_tracking_2d = True
            # Start fresh 2D tracking from this moment
            if self.selected_player_id in self.player_positions:
                self.tracking_start_index = len(self.player_positions[self.selected_player_id])

    def _update_player_stats(self, player_id, curr_pos):
        """Update statistics display for selected player"""
        if player_id != self.selected_player_id:
            return

        # Get all positions for the player
        positions = self.player_positions[player_id]
        if not positions:
            return

        # Calculate time
        frame_number = self.video_state.current_frame
        time_in_seconds = frame_number / self.video_state.fps
        minutes = int(time_in_seconds // 60)
        seconds = int(time_in_seconds % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        # Calculate velocity (using last two positions)
        if len(positions) >= 2:
            prev_pos = positions[-2]
            distance = ((curr_pos[0] - prev_pos[0]) ** 2 + (curr_pos[1] - prev_pos[1]) ** 2) ** 0.5
            time_between_frames = 1 / self.video_state.fps
            velocity = distance / time_between_frames

            # Update statistics display with larger text
            stats_text = f"Player ID: {player_id}\n\n"  # Added extra newline for spacing
            stats_text += f"Time: {time_str}\n\n"  # Video time format
            stats_text += f"Position: ({int(curr_pos[0])}, {int(curr_pos[1])})\n\n"
            stats_text += f"Velocity: {velocity:.1f} px/s"  # Simplified decimal places

            self.stats_text.configure(state="normal")
            self.stats_text.delete("1.0", tk.END)
            self.stats_text.insert("1.0", stats_text)
            self.stats_text.configure(state="disabled")

    def _clear_tracking(self):
        """Clear tracking data for selected player"""
        if self.selected_player_id in self.player_positions:
            self.player_positions[self.selected_player_id] = []
            self.stats_text.configure(state="normal")
            self.stats_text.delete("1.0", tk.END)
            self.stats_text.configure(state="disabled")

    def update_player_tracking(self, frame):
        """Update player tracking with YOLO detections"""
        if not self.video_state.is_playing:
            return

        try:
            # Run YOLO detection less frequently
            should_detect = self.video_state.current_frame % 2 == 0  # Process every other frame

            if should_detect:
                # Run YOLO detection
                results = self.model(frame, verbose=False)

                # Process detections
                if len(results) > 0:
                    boxes = results[0].boxes
                    current_detections = {}

                    # First, get all current detections
                    for box in boxes:
                        if int(box.cls) == 0:  # person class
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                            current_detections[center] = (x1, y1, x2, y2)

                    # Match current detections with previous positions
                    matched_ids = {}
                    for center in current_detections:
                        min_dist = float('inf')
                        matched_id = None

                        # Check distance to all previous positions
                        for player_id, last_pos in self.last_positions.items():
                            dist = ((center[0] - last_pos[0]) ** 2 + (center[1] - last_pos[1]) ** 2) ** 0.5
                            if dist < min_dist and dist < 30:  # Reduced threshold from 100 to 30
                                min_dist = dist
                                matched_id = player_id

                        if matched_id is None:
                            matched_id = self.next_id
                            self.next_id += 1

                        matched_ids[center] = matched_id
                        self.last_positions[matched_id] = center
                        current_detections[center] = (
                        *current_detections[center], matched_id)  # Store ID with detection

                    # Update current detections for this frame
                    self.current_detections = current_detections

                    # Update positions for tracking
                    for center, (x1, y1, x2, y2, player_id) in current_detections.items():
                        if player_id not in self.player_positions:
                            self.player_positions[player_id] = []
                        self.player_positions[player_id].append(center)
                        self._update_player_stats(player_id, center)

                    # Update dropdown less frequently
                    if self.video_state.current_frame % 10 == 0:
                        player_list = [f"Player {i}" for i in sorted(self.last_positions.keys())]
                        if player_list:
                            self.player_dropdown.configure(values=player_list, state="normal")

            # Always draw boxes using the last known positions
            if hasattr(self, 'current_detections'):
                for center, (x1, y1, x2, y2, player_id) in self.current_detections.items():
                    color = (0, 0, 255) if player_id == self.selected_player_id else (255, 0, 0)

                    # Draw box
                    cv2.rectangle(frame,
                                  (int(x1), int(y1)),
                                  (int(x2), int(y2)),
                                  color, 2)

                    # Draw ID
                    cv2.putText(frame,
                                f"ID: {player_id}",
                                (int(x1), int(y1) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                color,
                                2)

            # Display frame
            frame = cv2.resize(frame, (800, 600))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            self.video_display.configure(image=img_tk)
            self.video_display.image = img_tk

            # Update visualizations less frequently
            if self.video_state.current_frame % 5 == 0:
                self._update_pitch_visualization()
                self._update_heatmap()

        except Exception as e:
            print(f"Tracking error: {str(e)}")

    def _update_pitch_visualization(self):
        """Update the 2D pitch visualization with player movement"""
        if not self.is_tracking_2d or self.selected_player_id not in self.player_positions:
            return

        # Get only positions since tracking started
        all_positions = self.player_positions[self.selected_player_id]
        if not hasattr(self, 'tracking_start_index'):
            return

        positions = all_positions[self.tracking_start_index:]
        if len(positions) < 2:
            return

        # Clear previous drawings
        self.pitch_canvas_right.delete("movement")

        # Get canvas dimensions
        width = self.pitch_canvas_right.winfo_width()
        height = self.pitch_canvas_right.winfo_height()
        margin_x = width * 0.1
        margin_y = height * 0.1
        field_width = width - (2 * margin_x)
        field_height = height - (2 * margin_y)

        # Draw movement lines for 2D positions
        for i in range(1, len(positions)):
            x1 = margin_x + (positions[i - 1][0] / 800) * field_width
            y1 = margin_y + (positions[i - 1][1] / 600) * field_height
            x2 = margin_x + (positions[i][0] / 800) * field_width
            y2 = margin_y + (positions[i][1] / 600) * field_height

            self.pitch_canvas_right.create_line(
                x1, y1, x2, y2,
                fill='red', width=2,
                tags="movement"
            )

        # Draw current position
        if positions:
            last_pos = positions[-1]
            x = margin_x + (last_pos[0] / 800) * field_width
            y = margin_y + (last_pos[1] / 600) * field_height
            self.pitch_canvas_right.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill='red', outline='white',
                tags="movement"
            )

    def _update_heatmap(self):
        """Update the heatmap visualization with more red gradient - continuous effect"""
        if self.selected_player_id not in self.player_positions:
            return

        # Clear previous heatmap
        self.pitch_canvas_left.delete("heatmap")

        positions = self.player_positions[self.selected_player_id]
        if not positions:
            return

        # Get canvas dimensions
        width = self.pitch_canvas_left.winfo_width()
        height = self.pitch_canvas_left.winfo_height()

        # Create heatmap data array
        heatmap_data = np.zeros((height, width))

        # Convert positions to heatmap coordinates and add more weight to recent positions
        for i, pos in enumerate(positions):
            x = int((pos[0] / 800) * width)
            y = int((pos[1] / 600) * height)
            if 0 <= x < width and 0 <= y < height:
                # Add more weight to recent positions with continuous effect
                weight = 1 + (i / len(positions)) * 2  # Increased weight factor
                heatmap_data[y, x] += weight

        # Apply Gaussian filtering with smaller sigma for sharper heatmap
        heatmap_data = gaussian_filter(heatmap_data, sigma=10)

        # Normalize the data
        if heatmap_data.max() > 0:
            heatmap_data = heatmap_data / heatmap_data.max()

        # Create colormap (predominantly red with continuous effect)
        for y in range(height):
            for x in range(width):
                if heatmap_data[y, x] > 0.01:  # Threshold to avoid very faint colors
                    # Calculate color intensity with continuous effect
                    intensity = heatmap_data[y, x]

                    # Modify color calculation to favor red with continuous effect
                    red = 255
                    green = int(200 * intensity * 0.5)  # Reduced green component for more redness

                    # Create color with continuous effect
                    color = f'#{red:02x}{green:02x}00'

                    # Draw larger pixels for better visibility with continuous effect
                    pixel_size = 3  # Increased pixel size

                    self.pitch_canvas_left.create_rectangle(
                        x, y, x + pixel_size, y + pixel_size,
                        fill=color,
                        outline='',
                        tags="heatmap",
                        stipple='gray50'  # Changed stipple pattern for better visibility
                    )


if __name__ == "__main__":
    app = FootballTrackerGUI()
    app.run()