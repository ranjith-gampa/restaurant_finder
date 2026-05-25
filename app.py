from flask import Flask, render_template, request

from search import GooglePlacesClient, rank_and_filter_restaurants


app = Flask(__name__)


@app.get("/")
def index():
    query = request.args.get("query", "").strip()
    location = request.args.get("location", "").strip()
    selected_filters = [value.strip().lower() for value in request.args.getlist("filter") if value.strip()]

    restaurants: list[dict] = []
    filters: list[dict] = []
    error_message = ""

    if query:
        try:
            client = GooglePlacesClient.from_env()
            raw_results = client.search_restaurants(query=query, location=location or None)
            restaurants, filters = rank_and_filter_restaurants(
                candidates=raw_results,
                query=query,
                required_terms=selected_filters,
            )
        except Exception as error:  # noqa: BLE001
            error_message = str(error)

    return render_template(
        "index.html",
        query=query,
        location=location,
        selected_filters=selected_filters,
        restaurants=restaurants,
        filters=filters,
        error_message=error_message,
    )


if __name__ == "__main__":
    app.run()
