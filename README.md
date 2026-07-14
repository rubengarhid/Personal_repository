# Clasificación de Clientes Mayoristas con XGBoost (Horeca vs Retail)

**Autor:** Rubén Garrido Hidalgo
**Stack:** Python · XGBoost · Scikit-learn · Pandas · Matplotlib

## 📌 Problema de negocio

Un distribuidor mayorista vende a dos tipos de clientes: canal **Horeca**
(Hoteles, Restaurantes, Cafeterías) y canal **Retail** (minorista). Saber a qué
canal pertenece un cliente nuevo, a partir de su patrón de gasto, permite
ajustar la estrategia comercial, logística y de precios sin depender de un
registro manual.

Este proyecto entrena un modelo de clasificación con **XGBoost** para predecir
el canal de venta a partir del gasto anual del cliente en 6 categorías de
producto y su región geográfica.

## 📊 Dataset

[Wholesale customers — UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/Wholesale+customers)
440 clientes de un distribuidor portugués, 8 variables:

| Variable | Tipo | Descripción |
|---|---|---|
| Channel (target) | Categórica | 1 = Horeca, 2 = Retail |
| Region | Categórica | Región del cliente |
| Fresh, Milk, Grocery, Frozen, Detergents_Paper, Delicassen | Continua | Gasto anual (u.m.) por categoría de producto |

## ⚙️ Metodología

1. **EDA**: revisión de tipos, nulos (0) y estadística descriptiva.
2. **Preprocesado**: `Region` se codifica con One-Hot Encoding por ser una
   variable nominal, no ordinal.
3. **Split**: 80/20 estratificado por clase.
4. **Ajuste de hiperparámetros**: `RandomizedSearchCV` (5-fold estratificado,
   optimizando ROC-AUC) sobre `max_depth`, `learning_rate`, `n_estimators`,
   `subsample` y `colsample_bytree`.
5. **Validación cruzada con early stopping** (`xgb.cv`) para fijar el número
   óptimo de árboles y evitar sobreajuste.
6. **Evaluación**: accuracy, ROC-AUC, matriz de confusión y
   `classification_report` (precision, recall, F1 por clase).
7. **Importancia de variables** con la métrica `gain` (impacto real en la
   reducción del error, no solo frecuencia de uso).

## ✅ Resultados

- **Accuracy en test:** ~92%
- **Variables más influyentes:** `Grocery`, `Detergents_Paper` y `Delicassen`
- El modelo discrimina bien entre canales pese al desbalance de clases
  (~70% Horeca / ~30% Retail) y al tamaño reducido del dataset.

![Importancia de variables](feature_importance.png)
![Matriz de confusión](confusion_matrix.png)

## ⚠️ Limitaciones

- Dataset pequeño (440 filas) y localizado en Portugal — la generalización a
  otros mercados no está garantizada.
- Clases desbalanceadas (70/30); no se ha aplicado remuestreo (SMOTE) ni
  `scale_pos_weight`.
- No se compara con otros algoritmos (Random Forest, Regresión Logística)
  como baseline.

## 🚀 Cómo ejecutarlo

```bash
git clone <url-del-repo>
cd wholesale-xgboost
pip install -r requirements.txt
jupyter notebook Wholesale_Customers_XGBoost.ipynb
```

Descarga `Wholesale customers data.csv` desde el
[repositorio UCI](https://archive.ics.uci.edu/ml/datasets/Wholesale+customers)
y colócalo en la misma carpeta que el notebook.

## 📁 Estructura del repositorio

```
├── Wholesale_Customers_XGBoost.ipynb   # Notebook completo
├── requirements.txt                     # Dependencias
├── feature_importance.png               # Gráfico generado
├── confusion_matrix.png                 # Gráfico generado
└── README.md
```
