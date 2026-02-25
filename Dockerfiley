FROM python:3.9-slim

# A konténeren belüli mappa neve
WORKDIR /magyartv

# Szükséges csomagok telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# A forráskód másolása
COPY . .

# Jogosultságok megadása a scriptnek
RUN chmod +x magyartv.py

# Indítás
CMD ["python", "magyartv.py"]
