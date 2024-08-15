from main import get_init_file_path, release_addon, set_plugin_version, zip_folder, ACTIVE_ADDON, DEFAULT_RELEASE_DIR
import sys, os

# The name of the addon to be released, this name is defined in the config.py of the addon as __addon_name__
addon_name_to_release = ACTIVE_ADDON
# addon_name_to_release = "new_addon"

def get_version_tag():
    args = sys.argv[1:]
    try:
        tag_idx = args.index("--tag")
    except:
        return None
    parts = args[tag_idx+1].split('.')
    assert len(parts) == 3
    return list(map(int, parts))

def try_zip_only(release_dir):    

    args = sys.argv[1:]
    try:
        zip_only_idx = args.index("--zip-only")
    except:
        return None
    if zip_only_idx is not None:
        name = args[zip_only_idx+1:zip_only_idx+2]
        name = name[0] if len(name) > 0 else None

        if not os.path.isdir(release_dir):
            raise ValueError("Cannot patch release: No release dir found!")
        release_folder = os.path.join(release_dir, name if name else addon_name_to_release)

        print("Zipping existing release bundle...")
        print(release_folder)
        zip_folder(os.path.join(release_dir, addon_name_to_release), release_folder)
        return True
    return False

if __name__ == '__main__':

    release_dir = DEFAULT_RELEASE_DIR

    tag_ver = get_version_tag()
    if tag_ver is not None:

        if not os.path.isdir(release_dir):
            raise ValueError("Cannot patch release: No release dir found!")
        release_folder = os.path.join(release_dir, addon_name_to_release)

        version = ".".join(map(str, tag_ver))
        print(f"Patching release with version {version}...")
        set_plugin_version(os.path.join(release_folder, "__init__.py"), tag_ver[0], tag_ver[1], tag_ver[2])
        try_zip_only(release_dir)
    else:
        if try_zip_only(release_dir):
            sys.exit(0)
        
        need_zip = not ("--no-zip" in sys.argv[1::])
        release_addon(get_init_file_path(addon_name_to_release), addon_name_to_release, False, release_dir, need_zip)
        if not need_zip:
            print("Add-on zipping skipped.")
