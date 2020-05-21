# coding=utf-8
"""
Building encyclopedia contains parameters used to compute interest function for each building / scenario
"""

BUILDING_ENCYCLOPEDIA = {

    "Flat_scenario": {

        "Sociability": {
            "house-house": (5, 7, 100),
            "house-crop": (57, 30, 100),
            "house-windmill": (15, 20, 100),
            "crop-crop": (20, 30, 100),
            "crop-house": (20, 30, 100),
            "crop-windmill": (25, 35, 100),
            "windmill-windmill": (20, 20, 100),
            "windmill-house": (25, 35, 100),
            "windmill-crop": (25, 35, 100)
        },

        "Accessibility": {
            "house": (5, 10, 25),
            "crop": (5, 10, 25),
            "windmill": (10, 15, 35)
        },

        "Weighting_factors": {
            "house": (0.5, 0.5),
            "crop": (0.5, 0.5),
            "windmill": (0.5, 0.5)

        }
    }
}