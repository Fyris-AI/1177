import pandas as pd
from openpyxl import Workbook

# Create data
data = {
    "Ålder / Period": [
        "14 år","14 år","17 år","19 år","30–40 år","50 år","50 år","54 år",
        "58 år","59 år","60 år","62 år","64 år","67 år","68 år","68 år",
        "68 år","69 år – aktuellt","69 år – aktuellt","69 år – aktuellt","67 år","68 år"
    ],
    "Undersökning": [
        "Röntgen underben","Akuta labprover","Röntgen handled","Röntgen nyckelben",
        "Allmän hälsokontroll","Lab, riskfaktorer","EKG","Ultraljud hjärta",
        "Röntgen knä (vänster)","Postop knäprotes","PSA","Ultraljud urinvägar",
        "Metabola lab","PSA","MRT hjärna","Kognitiv utredning",
        "Lab för minnesutredning","Allmän lab","Metabola markörer",
        "EKG","Lungröntgen","Ultraljud hjärta"
    ],
    "Resultat": [
        "Spiralfraktur tibia, reponerad, fibula intakt",
        "Hb 143 g/L, CRP <5 mg/L, elektrolyter normala",
        "Distal radiusfraktur med lätt dorsal vinkling",
        "Odislocerad medial klavikelfraktur",
        "Normala prover, ingen hypertoni ännu",
        "HbA1c 38 mmol/mol, LDL 4.2 mmol/L, TG 2.1 mmol/L, BMI 31",
        "Sinusrytm, lätt LVH",
        "Normal EF, lätt LVH",
        "Avancerad medial ledspringeförträngning, osteofyter → artros",
        "Protes i gott läge, ingen lossning",
        "2.2 µg/L",
        "Prostata 45 g, residualurin 80 ml, njurar ua",
        "HbA1c 45 mmol/mol, LDL 2.5 mmol/L, eGFR 72 ml/min",
        "3.1 µg/L (åldersadekvat)",
        "Mild global atrofi, lätt leukoarios, ingen stroke",
        "MMT 27/30, klocktest lätt nedsatt",
        "B12 310, folat 7.5, TSH 2.3, Ca 2.32, CRP <5",
        "Hb 144, Na 139, K 3.9, Kreatinin 96, eGFR 68",
        "HbA1c 46, LDL 2.0, HDL 1.1, TG 1.7",
        "Sinus 69/min, stabil lätt LVH",
        "Normalt hjärta, lätt aortaskleros",
        "EF 60%, lätt LVH, klaffar ua"
    ]
}

df = pd.DataFrame(data)

# Save to xlsx
file_path = "backend/data/patient_undersokningar.xlsx"
df.to_excel(file_path, index=False)

file_path