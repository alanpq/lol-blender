from main import test_addon, ACTIVE_ADDON

# The name of the addon to be tested, this name is defined in the config.py of the addon as __addon_name__
addon_name_to_test = ACTIVE_ADDON
# addon_name_to_test = "new_addon"

if __name__ == '__main__':
    test_addon(addon_name_to_test, enable_watch=True)
