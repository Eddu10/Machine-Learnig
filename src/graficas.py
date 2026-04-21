import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
import joblib
import xgboost as xgb
import warnings

warnings.filterwarnings('ignore')

print("--- VISOR INSTANTÁNEO DE GRÁFICAS ---")

print("Cargando IA, traductor y datos de examen...")
modelo_xgb = joblib.load('cerebro_xgboost.pkl')
codificador = joblib.load('traductor_etiquetas.pkl')
clases_detectadas = codificador.classes_

X_test = joblib.load('datos_examen_X.pkl')
y_test = joblib.load('datos_examen_y.pkl')

print("\n1. Generando Ranking de Sensores Críticos...")
ax = xgb.plot_importance(modelo_xgb, importance_type='weight', max_num_features=10,
                         height=0.5, title='Ranking: Sensores Críticos')
fig_importancia = ax.figure
fig_importancia.set_size_inches(12, 6)
plt.tight_layout()
plt.show()

print("\nCalculando predicciones...")
predicciones = modelo_xgb.predict(X_test)

print("\n2. Generando Matriz de Confusión...")
fig, ax = plt.subplots(figsize=(20, 12))

ConfusionMatrixDisplay.from_predictions(
    y_test,
    predicciones,
    display_labels=clases_detectadas,
    xticks_rotation=45,
    cmap='Blues',
    values_format=',',
    ax=ax
)

plt.title('Matriz de Confusión: Aciertos vs Errores de XGBoost', fontsize=22, pad=20)
plt.xlabel('Lo que predijo la IA', fontsize=16, labelpad=15)
plt.ylabel('La falla real', fontsize=16, labelpad=15)
plt.xticks(fontsize=11, ha='right')
plt.yticks(fontsize=11)
plt.tight_layout()

plt.show()

print("\n¡Visualización completada!")