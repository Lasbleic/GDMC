# Name to display in MCEdit filter menu
from flat_settlement import FlatSettlement

displayName = "Create a settlement"

# Dictionary representing different options
inputs = ()


# Necessary function to be considered as a filter by MCEdit. This is the function that will be executed when the filter
# will be applied

def perform(level, box, options):
    print("Hello World!")
    settlement = FlatSettlement(box)
    settlement.generate(level)
