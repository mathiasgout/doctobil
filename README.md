# Doctobil

Extract the list of doctors in the order in which they appear on the doctolib website and application, based on their speciality and location.

## Instalation
Install from the github repository:
```bash
pip install git+https://github.com/mathiasgout/doctobil.git -U
```

## Exemple
```python
from doctobil import Doctobil

doctobil = Doctobil(speciality="Ostéopathe", place="75014")
results = doctobil.extract_data()

print(results) 
# [{'page': 1, 'id': '9868***', 'url': '/osteopathe/paris/emman****?pid=practice-11***', 'full_name': 'Mme Emm*** *** ***', 'total_availabilities': 6}, ...]
```