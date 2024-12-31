import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QFileDialog, QFrame, QComboBox, QDialog, QGridLayout, QSlider,
                             QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt

class HistogramWindow(QDialog):
    def __init__(self, image, title="Histogram"):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 600, 400)

        # Generate histogram as an image
        histogram_image = self.generate_histogram_image(image)

        # Display the histogram
        self.histogram_label = QLabel(self)
        self.histogram_label.setPixmap(histogram_image)
        self.histogram_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.histogram_label)
        self.setLayout(layout)

    def generate_histogram_image(self, image):
        # Compute the histogram
        histogram, bin_edges = np.histogram(image, bins=256, range=(0, 255))

        # Create a blank canvas for the histogram
        hist_height = 300
        hist_width = 512
        hist_image = np.full((hist_height, hist_width, 3), 255, dtype=np.uint8)

        # Normalize the histogram to fit the height of the canvas
        max_value = max(histogram)
        if max_value > 0:
            normalized_histogram = (histogram / max_value) * hist_height
        else:
            normalized_histogram = histogram

        # Draw the histogram
        for i in range(1, len(bin_edges)):
            x1 = int((i - 1) * (hist_width / 256))
            x2 = int(i * (hist_width / 256))
            y1 = hist_height - int(normalized_histogram[i - 1])
            y2 = hist_height

            cv2.rectangle(hist_image, (x1, y1), (x2, y2), (0, 0, 0), -1)

        # Convert to QPixmap
        height, width, channel = hist_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(hist_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_image)

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Quality Viewer")
        self.setGeometry(100, 100, 1200, 400)

        self.input_image = None
        self.output1_image = None
        self.output2_image = None

        self.original_input_image = None
        self.original_output1_image = None
        self.original_output2_image = None

        self.init_ui()

    def init_ui(self):
        # Main Widget and Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # Image Display Area
        display_layout = QHBoxLayout()
        display_layout.addWidget(self.create_image_frame("Input Image", "input_label"))
        display_layout.addWidget(self.create_image_frame("Output 1", "output1_label"))
        display_layout.addWidget(self.create_image_frame("Output 2", "output2_label"))
        main_layout.addLayout(display_layout)

        # Controls Layout
        controls_layout = QVBoxLayout()

        # Load Image Controls
        load_layout = QHBoxLayout()
        load_btn = QPushButton("Load Image")
        load_btn.clicked.connect(self.load_image)
        load_layout.addWidget(load_btn)

        self.apply_on_combo = QComboBox()
        self.apply_on_combo.addItems(["Input", "Output 1", "Output 2"])
        load_layout.addWidget(self.apply_on_combo)

        self.output_combo = QComboBox()
        self.output_combo.addItems(["Output 1", "Output 2"])
        load_layout.addWidget(self.output_combo)

        controls_layout.addLayout(load_layout)

        # Enhancement Controls
        enhancement_layout = QHBoxLayout()
        self.contrast_type_combo = QComboBox()
        self.contrast_type_combo.addItems(["Histogram Equalization", "CLAHE", "Gamma Correction"])
        enhancement_layout.addWidget(self.contrast_type_combo)

        enhance_contrast_btn = QPushButton("Enhance Contrast")
        enhance_contrast_btn.clicked.connect(self.enhance_contrast)
        enhancement_layout.addWidget(enhance_contrast_btn)

        controls_layout.addLayout(enhancement_layout)

        # Zoom Controls
        zoom_layout = QHBoxLayout()
        self.zoom_factor_combo = QComboBox()
        self.zoom_factor_combo.addItems(
            ["5x", "4.5x", "4x", "3.5x", "3x", "2.5x", "2x", "1.75x", "1.5x", "1.25x", "1x", "0.75x", "0.5x", "0.25x"]
        )
        zoom_layout.addWidget(self.zoom_factor_combo)

        self.interpolation_combo = QComboBox()
        self.interpolation_combo.addItems(["Nearest-Neighbor", "Linear", "Bilinear", "Cubic"])
        zoom_layout.addWidget(self.interpolation_combo)

        zoom_btn = QPushButton("Apply Zoom")
        zoom_btn.clicked.connect(self.apply_zoom)
        zoom_layout.addWidget(zoom_btn)

        controls_layout.addLayout(zoom_layout)

        # Noise and Filter Controls
        noise_filter_layout = QHBoxLayout()
        self.noise_type_combo = QComboBox()
        self.noise_type_combo.addItems(["Gaussian", "Salt and Pepper", "Speckle"])
        noise_filter_layout.addWidget(self.noise_type_combo)

        add_noise_btn = QPushButton("Add Noise")
        add_noise_btn.clicked.connect(self.add_noise)
        noise_filter_layout.addWidget(add_noise_btn)

        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["Gaussian", "Bilateral", "Non-Local Means", "Low-Pass", "High-Pass"])
        noise_filter_layout.addWidget(self.filter_type_combo)

        add_filter_btn = QPushButton("Add Filter")
        add_filter_btn.clicked.connect(self.add_filter)
        noise_filter_layout.addWidget(add_filter_btn)

        controls_layout.addLayout(noise_filter_layout)

        # Histogram Controls
        histogram_layout = QHBoxLayout()
        self.histogram_combo = QComboBox()
        self.histogram_combo.addItems(["Input", "Output 1", "Output 2"])
        histogram_layout.addWidget(self.histogram_combo)

        show_hist_btn = QPushButton("Show Histogram")
        show_hist_btn.clicked.connect(self.show_histogram)
        histogram_layout.addWidget(show_hist_btn)

        controls_layout.addLayout(histogram_layout)

        # Brightness and Contrast Sliders
        brightness_contrast_layout = QGridLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(-100)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(0)
        brightness_contrast_layout.addWidget(QLabel("Brightness:"), 0, 0)
        brightness_contrast_layout.addWidget(self.brightness_slider, 0, 1)

        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(200)
        self.contrast_slider.setValue(100)
        brightness_contrast_layout.addWidget(QLabel("Contrast:"), 1, 0)
        brightness_contrast_layout.addWidget(self.contrast_slider, 1, 1)

        apply_bc_btn = QPushButton("Apply B/C")
        apply_bc_btn.clicked.connect(self.apply_brightness_contrast)
        brightness_contrast_layout.addWidget(apply_bc_btn, 2, 0, 1, 2)

        controls_layout.addLayout(brightness_contrast_layout)

        # SNR and CNR Buttons
        snr_cnr_layout = QHBoxLayout()
        snr_btn = QPushButton("Calculate SNR")
        snr_btn.clicked.connect(self.calculate_snr)
        snr_cnr_layout.addWidget(snr_btn)

        cnr_btn = QPushButton("Calculate CNR")
        cnr_btn.clicked.connect(self.calculate_cnr)
        snr_cnr_layout.addWidget(cnr_btn)

        controls_layout.addLayout(snr_cnr_layout)

        main_layout.addLayout(controls_layout)
        main_widget.setLayout(main_layout)

    def create_image_frame(self, title, label_name):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)

        image_label = QLabel()
        image_label.setMinimumSize(350, 300)
        image_label.setAlignment(Qt.AlignCenter)
        setattr(self, label_name, image_label)

        layout.addWidget(title_label)
        layout.addWidget(image_label)
        frame.setLayout(layout)
        return frame

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
                                                   "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            self.input_image = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
            self.original_input_image = self.input_image.copy()
            self.display_image(self.input_image, self.input_label)

    def apply_zoom(self):
        # Determine the source image to apply zoom on
        source_image = None
        selected_image = self.apply_on_combo.currentText()

        if selected_image == "Input":
            source_image = self.input_image
        elif selected_image == "Output 1":
            source_image = self.output1_image
        elif selected_image == "Output 2":
            source_image = self.output2_image

        if source_image is None:
            QMessageBox.warning(self, "Error", "No image selected for zoom.")
            return

        # Get zoom factor
        zoom_factor = float(self.zoom_factor_combo.currentText().replace("x", ""))

        # Get interpolation method
        interpolation_method = self.interpolation_combo.currentText()
        if interpolation_method == "Nearest-Neighbor":
            interpolation = cv2.INTER_NEAREST
        elif interpolation_method == "Linear" or interpolation_method == "Bilinear":
            interpolation = cv2.INTER_LINEAR
        elif interpolation_method == "Cubic":
            interpolation = cv2.INTER_CUBIC
        else:
            interpolation = cv2.INTER_LINEAR

        try:
            # For zooming in (factor > 1), crop and resize the image
            if zoom_factor > 1:
                height, width = source_image.shape
                crop_width = int(width / zoom_factor)
                crop_height = int(height / zoom_factor)

                # Ensure the cropped section stays within bounds
                start_x = max((width - crop_width) // 2, 0)
                start_y = max((height - crop_height) // 2, 0)
                end_x = start_x + crop_width
                end_y = start_y + crop_height

                cropped_image = source_image[start_y:end_y, start_x:end_x]
                resized_image = cv2.resize(cropped_image, (width, height), interpolation=interpolation)

            # For zooming out (factor < 1), directly resize the image
            elif zoom_factor < 1:
                height, width = source_image.shape
                new_width = int(width * zoom_factor)
                new_height = int(height * zoom_factor)
                resized_image = cv2.resize(source_image, (new_width, new_height), interpolation=interpolation)

                # Add padding to fit the original size
                pad_width = (width - new_width) // 2
                pad_height = (height - new_height) // 2
                resized_image = cv2.copyMakeBorder(resized_image, pad_height, pad_height, pad_width, pad_width,
                                                   cv2.BORDER_CONSTANT, value=0)

            # If the factor is exactly 1, keep the image unchanged
            else:
                resized_image = source_image.copy()

            # Select the target output
            target_output = self.output_combo.currentText()
            if target_output == "Output 1":
                self.output1_image = resized_image
                self.display_image(resized_image, self.output1_label)
            elif target_output == "Output 2":
                self.output2_image = resized_image
                self.display_image(resized_image, self.output2_label)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during zoom operation: {e}")

    def enhance_contrast(self):
        # Determine the source image
        source_image = None
        selected_image = self.apply_on_combo.currentText()

        if selected_image == "Input":
            source_image = self.input_image
        elif selected_image == "Output 1":
            source_image = self.output1_image
        elif selected_image == "Output 2":
            source_image = self.output2_image

        if source_image is None:
            return

        # Apply selected contrast enhancement method
        enhanced_image = None
        contrast_type = self.contrast_type_combo.currentText()

        if contrast_type == "Histogram Equalization":
            enhanced_image = cv2.equalizeHist(source_image)

        elif contrast_type == "CLAHE":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_image = clahe.apply(source_image)


        elif contrast_type == "Gamma Correction":

            gamma = 1.2  # Adjust gamma value (<1 for darker, >1 for brighter)
            inv_gamma = 1.0 / gamma
            lookup_table = np.array([((i / 255.0) ** inv_gamma) * 255
                                     for i in range(256)]).astype("uint8")
            enhanced_image = cv2.LUT(source_image, lookup_table)

        # Determine the target output
        target_output = self.output_combo.currentText()
        target_label = None

        if target_output == "Output 1":
            self.output1_image = enhanced_image
            target_label = self.output1_label
        elif target_output == "Output 2":
            self.output2_image = enhanced_image
            target_label = self.output2_label

        # Display the enhanced image
        self.display_image(enhanced_image, target_label)

    def add_noise(self):
        # Determine the source image to apply noise on
        source_image = None
        target_label = None

        selected_image = self.apply_on_combo.currentText()
        if selected_image == "Input":
            source_image = self.input_image
        elif selected_image == "Output 1":
            source_image = self.output1_image
        elif selected_image == "Output 2":
            source_image = self.output2_image

        if source_image is None:
            return

        # Add noise based on the selected type
        noise_type = self.noise_type_combo.currentText()
        noisy_image = None
        if noise_type == "Gaussian":
            mean = 0
            stddev = 25  # Adjust standard deviation for noise intensity
            noise = np.random.normal(mean, stddev, source_image.shape).astype(np.float32)
            noisy_image = cv2.add(source_image.astype(np.float32), noise)
        elif noise_type == "Salt and Pepper":
            noisy_image = source_image.copy()
            prob = 0.02  # Proportion of pixels affected
            num_salt = int(prob * source_image.size * 0.5)
            num_pepper = int(prob * source_image.size * 0.5)

            # Add salt
            coords = [np.random.randint(0, i - 1, num_salt) for i in source_image.shape]
            noisy_image[coords[0], coords[1]] = 255

            # Add pepper
            coords = [np.random.randint(0, i - 1, num_pepper) for i in source_image.shape]
            noisy_image[coords[0], coords[1]] = 0
        elif noise_type == "Speckle":
            noise = np.random.randn(*source_image.shape) * 0.1
            noisy_image = source_image + source_image * noise

        noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)

        # Determine the target output
        target_output = self.output_combo.currentText()
        if target_output == "Output 1":
            self.output1_image = noisy_image
            target_label = self.output1_label
        elif target_output == "Output 2":
            self.output2_image = noisy_image
            target_label = self.output2_label

        # Display the noisy image
        self.display_image(noisy_image, target_label)

    def add_filter(self):
        # Determine the source image to apply filter on
        source_image = None
        target_label = None

        selected_image = self.apply_on_combo.currentText()
        if selected_image == "Input":
            source_image = self.input_image
        elif selected_image == "Output 1":
            source_image = self.output1_image
        elif selected_image == "Output 2":
            source_image = self.output2_image

        if source_image is None:
            return

        # Apply filter based on the selected type
        filter_type = self.filter_type_combo.currentText()
        filtered_image = None

        if filter_type == "Gaussian":
            filtered_image = cv2.GaussianBlur(source_image, (5, 5), 0)

        elif filter_type == "Bilateral":
            filtered_image = cv2.bilateralFilter(source_image, d=9, sigmaColor=75, sigmaSpace=75)

        elif filter_type == "Non-Local Means":
            filtered_image = cv2.fastNlMeansDenoising(source_image, None, 30, 7, 21)

        elif filter_type == "Low-Pass":
            # Apply Low-Pass filter using Fourier Transform
            dft = cv2.dft(np.float32(source_image), flags=cv2.DFT_COMPLEX_OUTPUT)
            dft_shift = np.fft.fftshift(dft)

            # Create a mask to keep only low frequencies
            rows, cols = source_image.shape[:2]
            crow, ccol = rows // 2, cols // 2
            mask = np.zeros((rows, cols, 2), np.uint8)
            r = 30  # Radius for low-pass filter
            center = [crow, ccol]
            cv2.circle(mask, center, r, (1, 1, 1), -1)

            # Apply mask and inverse DFT
            fshift = dft_shift * mask
            f_ishift = np.fft.ifftshift(fshift)
            img_back = cv2.idft(f_ishift)
            img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])

            # Normalize the magnitude to avoid noisy results
            img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX)
            filtered_image = np.uint8(img_back)

        elif filter_type == "High-Pass":
            # Apply High-Pass filter using Fourier Transform
            dft = cv2.dft(np.float32(source_image), flags=cv2.DFT_COMPLEX_OUTPUT)
            dft_shift = np.fft.fftshift(dft)

            # Create a mask to block low frequencies (high-pass filter)
            rows, cols = source_image.shape[:2]
            crow, ccol = rows // 2, cols // 2
            mask = np.ones((rows, cols, 2), np.uint8)
            r = 30  # Radius for high-pass filter
            center = [crow, ccol]
            cv2.circle(mask, center, r, (0, 0, 0), -1)

            # Apply mask and inverse DFT
            fshift = dft_shift * mask
            f_ishift = np.fft.ifftshift(fshift)
            img_back = cv2.idft(f_ishift)
            img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])

            # Normalize the magnitude to avoid noisy results
            img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX)
            filtered_image = np.uint8(img_back)

        # Determine the target output
        target_output = self.output_combo.currentText()
        if target_output == "Output 1":
            self.output1_image = filtered_image
            target_label = self.output1_label
        elif target_output == "Output 2":
            self.output2_image = filtered_image
            target_label = self.output2_label

        # Display the filtered image
        self.display_image(filtered_image, target_label)

    def apply_brightness_contrast(self):
        # Determine the source image
        source_image = None
        target_label = None
        selected_image = self.apply_on_combo.currentText()

        if selected_image == "Input":
            source_image = self.input_image
            if source_image is None: return
        elif selected_image == "Output 1":
            source_image = self.output1_image
        elif selected_image == "Output 2":
            source_image = self.output2_image
        else:
            return  # No source image selected

        # Get brightness and contrast values from sliders
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value() / 100.0  # Normalize to 0.0-2.0 range

        # Apply brightness and contrast
        adjusted_image = cv2.addWeighted(source_image, contrast, np.zeros_like(source_image), 0, brightness)
        adjusted_image = np.clip(adjusted_image, 0, 255).astype(np.uint8)  # Clip values to be valid pixel values

        # Determine the target output
        target_output = self.output_combo.currentText()
        if target_output == "Output 1":
            self.output1_image = adjusted_image
            target_label = self.output1_label
        elif target_output == "Output 2":
            self.output2_image = adjusted_image
            target_label = self.output2_label
        else:
            return

        self.display_image(adjusted_image, target_label)

    def display_image(self, image, label):
        if image is not None:
            height, width = image.shape
            bytes_per_line = width
            qt_image = QImage(image.data, width, height, bytes_per_line,
                              QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(label.size(), Qt.KeepAspectRatio)
            label.setPixmap(scaled_pixmap)

    def show_histogram(self):
        # Determine which image to display the histogram for
        selected_image = self.histogram_combo.currentText()
        image = None

        if selected_image == "Input":
            image = self.input_image
        elif selected_image == "Output 1":
            image = self.output1_image
        elif selected_image == "Output 2":
            image = self.output2_image

        if image is not None:
            # Show the histogram in a separate window
            histogram_window = HistogramWindow(image, title=f"{selected_image} Histogram")
            histogram_window.exec_()

    def calculate_snr(self):
        """Calculate Signal-to-Noise Ratio (SNR) for a selected image."""
        # Determine the source image
        source_image = None
        selected_image = self.apply_on_combo.currentText()

        if selected_image == "Input":
            source_image = self.input_image
        elif selected_image == "Output 1":
            source_image = self.output1_image
        elif selected_image == "Output 2":
            source_image = self.output2_image

        if source_image is None:
            QMessageBox.warning(self, "Error", "No image loaded or selected.")
            return

        # Ensure the image is grayscale
        if len(source_image.shape) == 3:
            source_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)

        # Clone the image for display
        clone_image = source_image.copy()

        # OpenCV ROI selection
        signal_roi = cv2.selectROI("Select ROI for Signal", clone_image, showCrosshair=False)
        noise_roi = cv2.selectROI("Select ROI for Noise", clone_image, showCrosshair=False)
        cv2.destroyAllWindows()

        # Validate ROIs
        if signal_roi == (0, 0, 0, 0) or noise_roi == (0, 0, 0, 0):
            QMessageBox.warning(self, "Error", "No ROI selected. Please select ROIs for both signal and noise.")
            return

        try:
            # Extract the ROIs
            signal = source_image[int(signal_roi[1]):int(signal_roi[1] + signal_roi[3]),
                     int(signal_roi[0]):int(signal_roi[0] + signal_roi[2])]
            noise = source_image[int(noise_roi[1]):int(noise_roi[1] + noise_roi[3]),
                    int(noise_roi[0]):int(noise_roi[0] + noise_roi[2])]

            if signal.size == 0 or noise.size == 0:
                raise ValueError("Selected ROI has zero area.")

            # Calculate mean signal and noise standard deviation
            mean_signal = np.mean(signal)
            std_noise = np.std(noise)

            # Calculate SNR
            snr = mean_signal / std_noise if std_noise != 0 else float('inf')

            # Display SNR
            snr_msg = f"SNR: {snr:.2f}" if std_noise != 0 else "SNR: Infinity (Noise Std is 0)"
            QMessageBox.information(self, "SNR Result", snr_msg)

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def calculate_cnr(self):
        """Calculate Contrast-to-Noise Ratio (CNR) for a selected image."""
        # Determine the source image
        source_image = None
        selected_image = self.apply_on_combo.currentText()

        if selected_image == "Input":
            source_image = self.input_image
        elif selected_image == "Output 1":
            source_image = self.output1_image
        elif selected_image == "Output 2":
            source_image = self.output2_image

        if source_image is None:
            QMessageBox.warning(self, "Error", "No image loaded or selected.")
            return

        # Ensure the image is grayscale
        if len(source_image.shape) == 3:
            source_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)

        # Clone the image for display
        clone_image = source_image.copy()

        # OpenCV ROI selection
        region1_roi = cv2.selectROI("Select ROI for Region 1 (Signal)", clone_image, showCrosshair=False)
        region2_roi = cv2.selectROI("Select ROI for Region 2 (Background)", clone_image, showCrosshair=False)
        noise_roi = cv2.selectROI("Select ROI for Noise", clone_image, showCrosshair=False)
        cv2.destroyAllWindows()

        # Validate ROIs
        if region1_roi == (0, 0, 0, 0) or region2_roi == (0, 0, 0, 0) or noise_roi == (0, 0, 0, 0):
            QMessageBox.warning(self, "Error", "No ROI selected. Please select ROIs for all regions.")
            return

        try:
            # Extract the ROIs
            region1 = source_image[int(region1_roi[1]):int(region1_roi[1] + region1_roi[3]),
                      int(region1_roi[0]):int(region1_roi[0] + region1_roi[2])]
            region2 = source_image[int(region2_roi[1]):int(region2_roi[1] + region2_roi[3]),
                      int(region2_roi[0]):int(region2_roi[0] + region2_roi[2])]
            noise = source_image[int(noise_roi[1]):int(noise_roi[1] + noise_roi[3]),
                    int(noise_roi[0]):int(noise_roi[0] + noise_roi[2])]

            if region1.size == 0 or region2.size == 0 or noise.size == 0:
                raise ValueError("One or more selected ROIs have zero area.")

            # Calculate mean intensities and noise standard deviation
            mean_region1 = np.mean(region1)
            mean_region2 = np.mean(region2)
            std_noise = np.std(noise)

            # Calculate CNR
            cnr = abs(mean_region1 - mean_region2) / std_noise if std_noise != 0 else float('inf')

            # Display CNR
            cnr_msg = f"CNR: {cnr:.2f}" if std_noise != 0 else "CNR: Infinity (Noise Std is 0)"
            QMessageBox.information(self, "CNR Result", cnr_msg)

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())