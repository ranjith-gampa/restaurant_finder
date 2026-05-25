# restaurant_finder

Restaurant search website built with Python + Flask.

## Features

- Search by any restaurant term (example: `vegetarian restaurants`)
- Uses Google Maps Places API to fetch restaurant candidates and reviews
- Ranks results by how strongly review text matches the search term
- Provides additional term-based filters from matched review keywords

## Run locally

```bash
python -m pip install -r requirements.txt
export GOOGLE_MAPS_API_KEY="your-api-key"
python app.py
```

Then open `http://127.0.0.1:5000/`.

## Tests

```bash
python -m unittest discover -s tests
```