from flask import request, jsonify
import os
import numpy as np
from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from werkzeug.utils import secure_filename
from accuracy import build_cnn, build_rnn, build_dnn

# Load models
base_model = VGG16(weights='imagenet')
cnn_model = build_cnn()
rnn_model = build_rnn()
dnn_model = build_dnn()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    image = load_img(image_path, target_size=(224, 224))
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)
    return image

def predict_breed(image_path):
    image = preprocess_image(image_path)
    
    # VGG16 Prediction
    preds = base_model.predict(image)
    decoded_preds = decode_predictions(preds, top=1)[0][0]  
    breed = decoded_preds[1].replace('_', ' ').title()
    base_confidence = decoded_preds[2] * 100
     

    # Ensure the input shape matches the models' expected format
    image = np.squeeze(image)  # Remove extra dimensions if any
    image = np.expand_dims(image, axis=0)  # Ensure shape (1, 224, 224, 3)

    # CNN, RNN, DNN Predictions
    cnn_preds = cnn_model.predict(image)  # No need for extra dimension
    rnn_preds = rnn_model.predict(image)  # Ensure correct shape
    dnn_preds = dnn_model.predict(image)  # Ensure correct shape

    return {
        "breed": breed,
        "base_confidence": f"{base_confidence:.2f}%",
        "cnn_accuracy": f"{np.max(cnn_preds) * 100:.2f}%",
        "rnn_accuracy": f"{np.max(rnn_preds) * 100:.2f}%",
        "dnn_accuracy": f"{np.max(dnn_preds) * 100:.2f}%"
    }

def init_routes(app):
    @app.route('/predict', methods=['POST'])
    def predict():
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"})

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(filepath)
                result = predict_breed(filepath)
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)})

        return jsonify({"error": "Invalid file format"})
