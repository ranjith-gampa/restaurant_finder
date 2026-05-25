import unittest

from search import rank_and_filter_restaurants, tokenize_search_query


class SearchRankingTests(unittest.TestCase):
    def test_tokenize_search_query(self):
        self.assertEqual(tokenize_search_query("Vegetarian restaurants!!"), ["restaurants", "vegetarian"])

    def test_rank_and_filter_prioritizes_review_matches(self):
        candidates = [
            {
                "name": "Green Bowl",
                "rating": 4.7,
                "user_ratings_total": 105,
                "types": ["restaurant", "food"],
                "reviews": [{"text": "Best vegetarian menu with plenty of vegetarian options."}],
            },
            {
                "name": "Random Diner",
                "rating": 4.8,
                "user_ratings_total": 300,
                "types": ["restaurant"],
                "reviews": [{"text": "Great burgers and steaks."}],
            },
        ]

        ranked, filters = rank_and_filter_restaurants(candidates, "vegetarian restaurants")

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["name"], "Green Bowl")
        self.assertGreater(ranked[0]["review_match_score"], 0)
        self.assertTrue(any(item["term"] == "vegetarian" for item in filters))

    def test_rank_and_filter_with_required_terms(self):
        candidates = [
            {
                "name": "Plant House",
                "rating": 4.5,
                "user_ratings_total": 80,
                "types": ["restaurant"],
                "reviews": [{"text": "Vegetarian and vegan options are excellent."}],
            },
            {
                "name": "Veg Spot",
                "rating": 4.3,
                "user_ratings_total": 40,
                "types": ["restaurant"],
                "reviews": [{"text": "Vegetarian dishes available."}],
            },
        ]

        ranked, _ = rank_and_filter_restaurants(candidates, "vegetarian vegan restaurants", required_terms=["vegan"])
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["name"], "Plant House")

    def test_required_terms_can_match_even_if_not_in_query(self):
        candidates = [
            {
                "name": "Ocean Plate",
                "rating": 4.1,
                "user_ratings_total": 22,
                "types": ["restaurant"],
                "reviews": [{"text": "Excellent gluten free options and fresh seafood."}],
            },
            {
                "name": "Basic Cafe",
                "rating": 4.2,
                "user_ratings_total": 35,
                "types": ["restaurant"],
                "reviews": [{"text": "Good coffee and pastries."}],
            },
        ]

        ranked, _ = rank_and_filter_restaurants(candidates, "seafood restaurants", required_terms=["gluten"])
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["name"], "Ocean Plate")


if __name__ == "__main__":
    unittest.main()
