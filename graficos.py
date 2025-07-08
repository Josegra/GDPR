# Supón que tu DataFrame en Spark se llama `df_spark`
df_pandas = df_spark.toPandas()

# Asegúrate de que la columna 'Fecha' sea de tipo datetime
df_pandas['Fecha'] = pd.to_datetime(df_pandas['Fecha'])


import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# === 1. Line plot ===
plt.figure(figsize=(12, 6))
for col in ['Corporate', 'Private', 'Supplier', 'CarMarket']:
    plt.plot(df_pandas['Fecha'], df_pandas[col], marker='o', label=col)
plt.title('Evolución por Segmento')
plt.xlabel('Fecha')
plt.ylabel('Volumen')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# === 2. Area chart ===
plt.figure(figsize=(12, 6))
plt.stackplot(
    df_pandas['Fecha'],
    df_pandas['Corporate'],
    df_pandas['Private'],
    df_pandas['Supplier'],
    df_pandas['CarMarket'],
    labels=['Corporate', 'Private', 'Supplier', 'CarMarket'],
    alpha=0.8
)
plt.title('Distribución Acumulada por Segmento (Área Apilada)')
plt.xlabel('Fecha')
plt.ylabel('Volumen Total')
plt.legend(loc='upper left')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# === 3. Pareto chart ===
totales = df_pandas[['Corporate', 'Private', 'Supplier', 'CarMarket']].sum().sort_values(ascending=False)
acumulado = totales.cumsum() / totales.sum() * 100

fig, ax1 = plt.subplots(figsize=(10, 6))
sns.barplot(x=totales.index, y=totales.values, color='skyblue', ax=ax1)
ax1.set_ylabel('Volumen Total')
ax1.set_title('Pareto por Segmento')

ax2 = ax1.twinx()
ax2.plot(totales.index, acumulado.values, color='red', marker='o', linestyle='--')
ax2.set_ylabel('Porcentaje Acumulado (%)')
ax2.axhline(80, color='gray', linestyle='dotted')
plt.tight_layout()
plt.show()

# === 4. Heatmap ===
heatmap_data = df_pandas.set_index('Fecha')[['Corporate', 'Private', 'Supplier', 'CarMarket']].T
plt.figure(figsize=(12, 4))
sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="YlGnBu", linewidths=.5)
plt.title('Heatmap de Volúmenes por Segmento y Fecha')
plt.xlabel('Fecha')
plt.ylabel('Segmento')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# === 5. Donut chart ===
totales = df_pandas[['Corporate', 'Private', 'Supplier', 'CarMarket']].sum()
fig, ax = plt.subplots(figsize=(6, 6))
wedges, texts, autotexts = ax.pie(
    totales, labels=totales.index, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3)
)
ax.set_title('Distribución Total por Segmento')
plt.tight_layout()
plt.show()
