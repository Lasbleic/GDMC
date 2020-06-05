import shutil as su
try:
    su.rmtree("./MCEdit/stock-filters/previous_settlement_filter")
except OSError:
    print("Didn't delete stock-filters/previous_settlement_filter as it does not exist")

try:
    # todo: previous filter debug before uncommenting
    # su.copytree("./MCEdit/stock-filters/settlement_filter", "./MCEdit/stock-filters/previous_settlement_filter")
    su.rmtree("./MCEdit/stock-filters/settlement_filter")
except OSError:
    print("Didn't copy then delete stock-filters/settlement_filter as it does not exist")
su.copytree("./src", "./MCEdit/stock-filters/settlement_filter")

try:
    su.rmtree("./MCEdit/stock-filters/custom_test_filters")
except OSError:
    print("Didn't copy then delete stock-filters/custom_test_filters as it does not exist")
su.copytree("./test", "./MCEdit/stock-filters/custom_test_filters")


