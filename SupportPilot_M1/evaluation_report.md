# SupportPilot - Milestone 1 Evaluation Report

| Test set | Tickets | Category acc. (target >= 90%) | Severity acc. (target >= 85%) | Avg time |
|---|---|---|---|---|
| Held-out set 1 | 174 | 94.3% (PASS) | 73.6% (BELOW TARGET) | 3.6 ms |
| Fresh held-out set 2 (v2) | 174 | 85.6% (BELOW TARGET) | 79.9% (BELOW TARGET) | 3.2 ms |

## Held-out set 1

### Category report
```
                       precision    recall  f1-score   support

        Account & App       1.00      0.83      0.91        24
     Charger Hardware       1.00      1.00      1.00        24
     Charging Session       0.80      1.00      0.89        24
    Payment & Billing       1.00      0.75      0.86        24
RFID & Authentication       0.86      1.00      0.92        24
        Safety Hazard       1.00      1.00      1.00        24
 Station Connectivity       1.00      1.00      1.00        30

             accuracy                           0.94       174
            macro avg       0.95      0.94      0.94       174
         weighted avg       0.95      0.94      0.94       174

```
### Severity report
```
              precision    recall  f1-score   support

    Critical       1.00      1.00      1.00        18
        High       0.77      0.69      0.73        54
         Low       0.68      0.71      0.70        42
      Medium       0.67      0.72      0.69        60

    accuracy                           0.74       174
   macro avg       0.78      0.78      0.78       174
weighted avg       0.74      0.74      0.74       174

```
### Severity confusion matrix (rows = actual, cols = predicted)
```
                 Low    Medium      High  Critical
       Low        30        12         0         0
    Medium         6        43        11         0
      High         8         9        37         0
  Critical         0         0         0        18
```

## Fresh held-out set 2 (v2)

### Category report
```
                       precision    recall  f1-score   support

        Account & App       1.00      1.00      1.00        24
     Charger Hardware       0.63      0.50      0.56        24
     Charging Session       1.00      0.75      0.86        24
    Payment & Billing       1.00      0.75      0.86        24
RFID & Authentication       0.80      1.00      0.89        24
        Safety Hazard       0.66      0.96      0.78        24
 Station Connectivity       1.00      1.00      1.00        30

             accuracy                           0.86       174
            macro avg       0.87      0.85      0.85       174
         weighted avg       0.87      0.86      0.85       174

```
### Severity report
```
              precision    recall  f1-score   support

    Critical       1.00      0.67      0.80        18
        High       0.79      0.74      0.77        42
         Low       0.79      0.81      0.80        54
      Medium       0.78      0.87      0.82        60

    accuracy                           0.80       174
   macro avg       0.84      0.77      0.80       174
weighted avg       0.81      0.80      0.80       174

```
### Severity confusion matrix (rows = actual, cols = predicted)
```
                 Low    Medium      High  Critical
       Low        44        10         0         0
    Medium         6        52         2         0
      High         6         5        31         0
  Critical         0         0         6        12
```

## Honest caveats
- Data is **synthetic** and written by the project author; it shows the pipeline works end-to-end.
- Round 1 (8 base complaints/category) scored ~70% category / ~74% severity on held-out set 1, so the training
  vocabulary was widened. Set 1 was used to diagnose that, so set 2 is the cleaner measurement.
- Re-run on real support tickets before quoting final accuracy.