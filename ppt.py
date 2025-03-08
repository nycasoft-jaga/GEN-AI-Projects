import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Sample dataset (Replace this with your actual dataset)
data = pd.DataFrame({
    'feature1': np.random.rand(100),
    'feature2': np.random.rand(100),
    'feature3': np.random.rand(100),
    'target': np.random.choice([0, 1], size=100)  # Ensure binary classification
})

# Splitting dataset
X = data.drop(columns=['target'])
y = data['target']

# Ensure y has at least two unique classes
unique_classes = np.unique(y)
if len(unique_classes) < 2:
    raise ValueError(f"Training data has only one class: {unique_classes}. Please check your data.")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest Classifier
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Predict probabilities
probabilities = rf.predict_proba(X_test)

# Ensure the classifier supports probability prediction
if probabilities.shape[1] == 2:
    prob = probabilities[:, 1]  # Probability of the positive class (1)
else:
    raise ValueError("Unexpected number of classes in predict_proba output. Check your dataset.")

# Predict labels
y_pred = rf.predict(X_test)

# Evaluate model
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2f}")
print(f"Predicted Probabilities: {prob}")
