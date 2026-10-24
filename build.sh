#!/bin/sh
# Builds tools/virusRender against the Gearmulator checkout in third_party/.
set -e
cd "$(dirname "$0")"

if [ ! -d third_party/gearmulator ]; then
	git clone --depth 1 --recurse-submodules --shallow-submodules \
		https://github.com/dsp56300/gearmulator third_party/gearmulator
fi

cmake -S third_party/gearmulator -B build -DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_OSX_ARCHITECTURES="$(uname -m)" \
	-DCMAKE_PROJECT_gearmulator_INCLUDE="$PWD/tools/gearmulator-inject.cmake" \
	-Dgearmulator_BUILD_JUCEPLUGIN=OFF \
	-Dgearmulator_BUILD_JUCEPLUGIN_CLAP=OFF \
	-Dgearmulator_BUILD_INSTALLER=OFF \
	-Dgearmulator_COMPONENT_DSPBRIDGE=OFF \
	-Dgearmulator_SYNTH_OSIRUS=OFF \
	-Dgearmulator_SYNTH_VAVRA=OFF \
	-Dgearmulator_SYNTH_XENIA=OFF \
	-Dgearmulator_SYNTH_NODALRED2X=OFF \
	-Dgearmulator_SYNTH_JE8086=OFF \
	-Dgearmulator_SYNTH_88EMU=OFF \
	-DBUILD_TESTING=OFF

JOBS="$(sysctl -n hw.ncpu 2>/dev/null || nproc)"
cmake --build build --target virusRender -j "$JOBS"
echo "built build/virusRender/virusRender"

# OB-Xf Python module for reference renders (tools/obxf_render.py)
if [ ! -d third_party/obxf ]; then
	git clone --depth 1 https://github.com/surge-synthesizer/OB-Xf third_party/obxf
	git -C third_party/obxf submodule update --init --recursive --depth 1
fi
git -C third_party/obxf apply --check "$PWD/tools/third_party_patches/obxf-python-matrix-target.patch" 2>/dev/null \
	&& git -C third_party/obxf apply "$PWD/tools/third_party_patches/obxf-python-matrix-target.patch"

PY="$PWD/.venv/bin/python"
# Configure from inside the checkout: its version stamp runs `git rev-parse HEAD` in the current directory
(cd third_party/obxf && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_OSX_ARCHITECTURES="$(uname -m)" -DOBXF_BUILD_PYTHON_BINDINGS=ON \
	-DPython_EXECUTABLE="$PY" -DPYTHON_EXECUTABLE="$PY" \
	&& cmake --build build --target obxfpy -j "$JOBS")
echo "built third_party/obxf/build/src/obxf-python/obxfpy"
