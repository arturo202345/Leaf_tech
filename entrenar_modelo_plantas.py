import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
import os
import pickle

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
dataset_path = "dataset_3"  # tu carpeta con subcarpetas por planta
img_size = (128, 128)
batch_size = 32
epochs = 10

# -----------------------------
# GENERADOR DE DATOS
# -----------------------------
datagen_train = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2,
    rotation_range=25,
    width_shift_range=0.2,
    height_shift_range=0.2,
    brightness_range=[0.8, 1.2],
    zoom_range=0.2,
    horizontal_flip=True,
)

train_gen = datagen_train.flow_from_directory(
    dataset_path,
    target_size=img_size,
    batch_size=batch_size,
    subset='training'
)

val_gen = datagen_train.flow_from_directory(
    dataset_path,
    target_size=img_size,
    batch_size=batch_size,
    subset='validation'
)

# -----------------------------
# MODELO CNN (Transfer Learning)
# -----------------------------
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(128,128,3))
base_model.trainable = False  # congelamos capas base

x = GlobalAveragePooling2D()(base_model.output)
x = Dense(256, activation='relu')(x)
output = Dense(train_gen.num_classes, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=output)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# -----------------------------
# ENTRENAMIENTO
# -----------------------------
history = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=epochs
)

# -----------------------------
# GUARDAR MODELO Y ETIQUETAS
# -----------------------------
model.save("modelo_plantas_cnn.h5")
with open("labels.pkl", "wb") as f:
    pickle.dump(train_gen.class_indices, f)

print("✅ Modelo CNN entrenado y guardado como 'modelo_plantas_cnn.h5'")
