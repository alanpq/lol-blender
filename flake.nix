{
  inputs = {
    # nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";

    # crane = {
    #   url = "github:ipetkov/crane";
    #   inputs.nixpkgs.follows = "nixpkgs";
    # };

    systems.url = "github:nix-systems/default";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    { self
    , systems
    , nixpkgs
    , treefmt-nix
    , ...
    } @ inputs:
    let
      eachSystem = f:
        nixpkgs.lib.genAttrs (import systems) (
          system:
          f (import nixpkgs {
            inherit system;
            overlays = [ inputs.rust-overlay.overlays.default ];
          })
        );

      rustToolchain = eachSystem (pkgs: pkgs.rust-bin.stable.latest);

      treefmtEval = eachSystem (pkgs: treefmt-nix.lib.evalModule pkgs ./treefmt.nix);
      venvDir = "venv";
    in
    {
      # You can use crane to build the Rust application with Nix

      # packages = eachSystem (pkgs: let
      #   craneLib = inputs.crane.lib.${pkgs.system};
      # in {
      #   default = craneLib.buildPackage {
      #     src = craneLib.cleanCargoSource (craneLib.path ./.);
      #   };
      # });

      devShells = eachSystem (pkgs: {
        # Based on a discussion at https://github.com/oxalica/rust-overlay/issues/129
        default = pkgs.mkShell (with pkgs; rec {
          nativeBuildInputs = [
            clang
            # Use mold when we are runnning in Linux
            (lib.optionals stdenv.isLinux mold)
          ];
          buildInputs = [
            rustToolchain.${pkgs.system}.default
            rust-analyzer-unwrapped
            clippy
            cargo

            python3
            python311Packages.pip
            python311Packages.virtualenv
            maturin
            # blender
            # pkg-config
            # openssl
          ];
          RUST_SRC_PATH = "${
            rustToolchain.${pkgs.system}.rust-src
          }/lib/rustlib/src/rust/library";

          BLENDER_PATH = "${blender}/bin/blender";
          BLENDER_VERSION = "4.1";

          shellHook = ''
            FLAKE_ROOT="$(git rev-parse --show-toplevel)"
            cd $FLAKE_ROOT
            if [ -d "${venvDir}" ]; then
              echo "Skipping venv creation, '${venvDir}' already exists"
            else
              echo "Creating new venv environment in path: '${venvDir}'"
              # Note that the module venv was only introduced in python 3, so for 2.7
              # this needs to be replaced with a call to virtualenv
              # python -m venv "${venvDir}"
              virtualenv -p $(which python) --always-copy "${venvDir}"
              # unescape to attempt use
              # \$\{pythonPackages.python.interpreter\} -m venv "${venvDir}"
            fi

            # activate our virtual env.
            source "${venvDir}/bin/activate"

            export WORK_DIR=`mktemp -d`

            function cleanup {      
              rm -rf "$WORK_DIR"
              echo "Deleted temp working directory $WORK_DIR"
            }

            # register the cleanup function to be called on the EXIT signal
            trap cleanup EXIT

            mkdir $WORK_DIR/addons
            export BLENDER_USER_SCRIPTS=$WORK_DIR
            export __BLENDER_ADDON_PATH=$WORK_DIR/addons/;
            export BLENDER_SYSTEM_PYTHON="$(which python)";
            export PYTHONPATH="$VIRTUAL_ENV/lib/site-packages";
            export PYTHONUSERBASE="$VIRTUAL_ENV";
            export __LOL_WHEEL_PATH="$FLAKE_ROOT/bindings/target/wheels/league_toolkit-0.1.0-cp311-cp311-manylinux_2_34_x86_64.whl";
            cd -
          '';

        });
      });

      formatter =
        eachSystem
          (pkgs: treefmtEval.${pkgs.system}.config.build.wrapper);

      checks = eachSystem (pkgs: {
        formatting = treefmtEval.${pkgs.system}.config.build.check self;
      });
    };
}



