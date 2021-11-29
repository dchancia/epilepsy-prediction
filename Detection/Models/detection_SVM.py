# Created by: Daniela Chanci Arrubla
# Description: Application of SVM to the features extracted from each patient of the
# publicly available dataset "UPenn and Mayo Clinic's Seizure Detection Challenge" downloaded
# from kaggle

import numpy as np
import pandas as pd
from pathlib import Path
from matplotlib import pyplot as plt
from collections import Counter
from imblearn.over_sampling import RandomOverSampler
from sklearn.utils import shuffle
from sklearn import svm, metrics
from sklearn.metrics import RocCurveDisplay, auc
from sklearn.svm import LinearSVC
from sklearn.model_selection import GridSearchCV, train_test_split, StratifiedKFold
from sklearn.feature_selection import SelectFromModel
from sklearn.preprocessing import StandardScaler
import warnings

# Ignore warnings
warnings.filterwarnings("ignore")

# Initialize list to print
toprint = []

# Load the extracted features
data = pd.read_csv(r"F:\Users\user\Desktop\EMORY\Classes\Fall_2021\CS_534\Project\Detection\Extracted_Features\Train\Dog_1_train.csv")
data = shuffle(data)
data = data.reset_index(drop=True)
X = data.drop(data.iloc[:, [-1]], axis=1) # Discard the class
X = StandardScaler().fit_transform(X) # Data Standardization
y = data.iloc[:, [-1]]
feature_names = data.columns[:-1]

# Print
toprint.append("Dog_1 Detection Summary")
toprint.append("1. One-second eeg segments: {}".format(X.shape[0]))
toprint.append("2. Extracted features: {}".format(X.shape[1]))

# Select best regularization parameter
est = LinearSVC(penalty="l1", dual=False)
c_grid = {'C': np.logspace(-3, 1, num=30)}
clf = GridSearchCV(estimator=est, param_grid=c_grid).fit(X, np.array(y))
reg_param = clf.best_params_['C']

# Feature selection
lsvc = LinearSVC(C=reg_param, penalty="l1", dual=False).fit(X, np.array(y))
model = SelectFromModel(lsvc, prefit=True)
X_reduced = model.transform(X)

# Print
toprint.append("3. Selected features: {}".format(X_reduced.shape[1]))
toprint.append("4. Selected features names:")
toprint.append(list(feature_names[model.get_support()]))

# Balance classes
ros = RandomOverSampler(random_state=42)
X_bal, y_bal = ros.fit_resample(X_reduced, np.array(y))
X_bal = StandardScaler().fit_transform(X_bal)

# X_bal = X_reduced
# y_bal = np.array(y)

# Print
toprint.append("5. Classes distribution before balancing:")
toprint.append(y.value_counts())
toprint.append("6. Classes distribution after balancing:")
toprint.append(Counter(y_bal))

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_bal, y_bal, test_size=0.2, random_state=42)

# Train SVM
svm_model = svm.SVC(kernel="linear", probability=True, random_state=42)
svm_model.fit(X_train, y_train)

# Evaluate model
y_hat = svm_model.predict(X_test)

# Metrics
acc = metrics.accuracy_score(y_test, y_hat)
f1 = metrics.f1_score(y_test, y_hat, average='macro')
precision = metrics.precision_score(y_test, y_hat, average='macro')
recall = metrics.recall_score(y_test, y_hat, average='macro')

#Print
toprint.append("7. Accuracy: {}".format(acc))
toprint.append("8. Precision: {}".format(precision))
toprint.append("9. Recall: {}".format(recall))
toprint.append("10. F1-score: {}".format(f1))

# Evaluate model CV
# Run classifier with cross-validation and plot ROC curves
cv = StratifiedKFold(n_splits=5)
classifier = svm.SVC(kernel="linear", probability=True, random_state=42)

tprs = []
aucs = []
mean_fpr = np.linspace(0, 1, 100)

fig, ax = plt.subplots()
for i, (train, test) in enumerate(cv.split(X_train, y_train)):
    classifier.fit(X_train[train], y_train[train])
    viz = RocCurveDisplay.from_estimator(
        classifier,
        X_train[test],
        y_train[test],
        name="ROC fold {}".format(i),
        alpha=0.3,
        lw=1,
        ax=ax,
    )
    interp_tpr = np.interp(mean_fpr, viz.fpr, viz.tpr)
    interp_tpr[0] = 0.0
    tprs.append(interp_tpr)
    aucs.append(viz.roc_auc)

ax.plot([0, 1], [0, 1], linestyle="--", lw=2, color="r", label="Chance", alpha=0.8)

mean_tpr = np.mean(tprs, axis=0)
mean_tpr[-1] = 1.0
mean_auc = auc(mean_fpr, mean_tpr)
std_auc = np.std(aucs)
ax.plot(
    mean_fpr,
    mean_tpr,
    color="b",
    label=r"Mean ROC (AUC = %0.2f $\pm$ %0.2f)" % (mean_auc, std_auc),
    lw=2,
    alpha=0.8,
)

std_tpr = np.std(tprs, axis=0)
tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
ax.fill_between(
    mean_fpr,
    tprs_lower,
    tprs_upper,
    color="grey",
    alpha=0.2,
    label=r"$\pm$ 1 std. dev.",
)

ax.set(
    xlim=[-0.05, 1.05],
    ylim=[-0.05, 1.05],
    title="Receiver operating characteristic example",
)
ax.legend(loc="lower right")

# Write file
for elem in toprint:
    print(elem)

plt.show()
