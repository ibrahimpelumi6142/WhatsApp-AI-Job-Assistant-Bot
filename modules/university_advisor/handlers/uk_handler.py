from ..utils.dataset_loader import load_dataset

# -------------------------------
# Dataset loaders
# -------------------------------
def _get_uk_unis():
    return load_dataset("uk", "universities.json")
def reply_cheapest_unis():
    unis = _get_uk_unis()
    tuition = {t["university_code"]: t for t in _get_uk_tuition()}
    ...

