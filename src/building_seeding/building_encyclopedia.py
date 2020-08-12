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

        "Altitude": {
            "house": (60, 68, 90),
            "crop": (65, 70, 80),
            "windmill": (65, 75, 95)
        },

        "Steepness": {
            "house": (0, 6),
            "crop": (0, 3),
            "windmill": (1, 5)
        },

        "RiverDistance": {
            "house": (10, 120),
            "crop": (5, 80),
            "windmill": (10, 150)
        },

        "OceanDistance": {
            "house": (10, 150),
            "crop": (30, 200),
            "windmill": (25, 200)
        },

        "LavaObstacle": {
            "house": (10, 20),
            "crop": (8, 15),
            "windmill": (10, 25)
        },

        # (accessibility, sociability, altitude, pure_water, sea_water, lava)
        "Weighting_factors": {
            "house": (1, 3, 2, 1, 1, 1, 1),
            "crop": (1, 3, 2, 2, 0, 1, 3),
            "windmill": (2, 4, 2, 0, 0, 1, 2)
        },

        "markov": {
            "house": {"house": 10, "crop": 7},
            "crop": {"crop": 10, "windmill": 4, "house": 6},
            "windmill": {"crop": 1}
        }
    }
}
