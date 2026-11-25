#!/usr/bin/env bash 

GEAR=fw-autotagger
IMAGE=flywheel/autotagger:$1
LOG=autotagger-$1-$2
dir=$3
# Command:
docker run -it --rm --entrypoint bash\
	-v ${dir}/unity/fw-gears/${GEAR}/app:/flywheel/v0/app\
	-v ${dir}/unity/fw-gears/${GEAR}/utils:/flywheel/v0/utils\
	-v ${dir}/unity/fw-gears/${GEAR}/run.py:/flywheel/v0/run.py\
	-v ${dir}/unity/fw-gears/${GEAR}/${LOG}/input:/flywheel/v0/input\
	-v ${dir}/unity/fw-gears/${GEAR}/${LOG}/output:/flywheel/v0/output\
	-v ${dir}/unity/fw-gears/${GEAR}/${LOG}/work:/flywheel/v0/work\
	-v ${dir}/unity/fw-gears/${GEAR}/${LOG}/config.json:/flywheel/v0/config.json\
	-v ${dir}/unity/fw-gears/${GEAR}/${LOG}/manifest.json:/flywheel/v0/manifest.json\
	$IMAGE
