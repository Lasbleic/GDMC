# coding=utf-8
"""
Building encyclopedia contains parameters used to compute interest function for each building / scenario
"""

BUILDING_ENCYCLOPEDIA = {

    "Flat_scenario": {

        "Sociability": {
            "house-house": (7, 10, 100),
            "house-crop": (20, 25, 100),
            "house-windmill": (20, 25, 100),
            "house-ghost": (1, 2, 100),
            "crop-crop": (7, 10, 100),
            "crop-house": (20, 25, 100),
            "crop-windmill": (7, 10, 100),
            "crop-ghost": (20, 25, 100),
            "windmill-windmill": (7, 10, 100),
            "windmill-house": (20, 25, 100),
            "windmill-crop": (7, 10, 100),
            "windmill-ghost": (20, 25, 100),
            "ghost-house": (1, 2, 100),
            "ghost-crop": (20, 25, 100),
            "ghost-windmill": (20, 25, 100)
        },

        "Accessibility": {
            "house": (7, 10, 25),
            "crop": (15, 20, 25),
            "windmill": (12, 20, 25)
        },

        "Weighting_factors": {
            "house": (0.25, 0.75),
            "crop": (0.25, 0.75),
            "windmill": (0.25, 0.75)

        }
    }
}
