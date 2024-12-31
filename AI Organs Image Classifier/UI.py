import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QPushButton, QFileDialog
from PIL import Image
from tensorflow.keras.utils import img_to_array
import tensorflow as tf
import numpy as np

# Load your trained model
model = tf.keras.models.load_model('Organ_classify.keras')
img_width, img_height = 180, 180  # Ensure these match your model's input dimensions
data_cat = ["Brain", "Heart", "Liver"]  # Replace with your actual class names


class ImageClassifierApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organ Classification App")
        self.setGeometry(300, 100, 400, 600)
        self.setStyleSheet("background-color: #f5f5f5;")  # Light background

        # Layout setup
        layout = QVBoxLayout()

        # Display for the uploaded image
        self.img_label = QLabel("No image loaded")
        self.img_label.setAlignment(QtCore.Qt.AlignCenter)
        self.img_label.setFixedSize(300, 300)
        self.img_label.setStyleSheet(
            """
            border: 2px solid #007BFF; 
            padding: 10px; 
            border-radius: 15px;
            background-color: #e0e0e0;
            """
        )
        layout.addWidget(self.img_label, alignment=QtCore.Qt.AlignCenter)

        # Prediction result display
        self.result_label = QLabel("")
        self.result_label.setAlignment(QtCore.Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF; margin-top: 10px;")
        layout.addWidget(self.result_label, alignment=QtCore.Qt.AlignCenter)

        # Button to upload image
        upload_button = QPushButton("Upload Image")
        upload_button.setStyleSheet(
            """
            QPushButton {
                background-color: #007BFF; 
                color: white; 
                padding: 10px; 
                border-radius: 10px; 
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            """
        )
        upload_button.clicked.connect(self.load_image)
        layout.addWidget(upload_button, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(layout)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.jpg)")
        if file_path:
            # Display the image in the label
            pixmap = QtGui.QPixmap(file_path).scaled(280, 280, QtCore.Qt.KeepAspectRatio,
                                                     QtCore.Qt.SmoothTransformation)
            self.img_label.setPixmap(pixmap)

            # Load and preprocess the image for the model
            image = Image.open(file_path).convert("L")  # Convert to grayscale
            image = image.resize((img_width, img_height))
            img_arr = img_to_array(image) / 255.0  # Normalize
            img_bat = np.expand_dims(img_arr, axis=0)  # Add batch dimension

            # Run the prediction
            self.predict_image(img_bat)

    def predict_image(self, img_bat):
        prediction = model.predict(img_bat)
        pred_class = data_cat[np.argmax(prediction)]
        pred_confidence = np.max(prediction) * 100
        self.result_label.setText(f"Predicted Organ: {pred_class}")
        print(pred_confidence)


# Run the application
app = QtWidgets.QApplication(sys.argv)
window = ImageClassifierApp()
window.show()
sys.exit(app.exec_())
