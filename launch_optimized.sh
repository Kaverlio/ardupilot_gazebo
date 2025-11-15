#!/bin/bash

# Gazebo Optimized Launch Script
# Allocates more resources and enables performance features

# Force NVIDIA GPU usage (PRIME offloading)
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export __VK_LAYER_NV_optimus=NVIDIA_only
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json

# Set Gazebo to use multiple threads
export GAZEBO_NUM_THREADS=8

# Enable GPU acceleration for rendering
export LIBGL_ALWAYS_SOFTWARE=0

# Increase process priority (requires no password sudo or run as user)
# Higher priority = more CPU time allocation
cd ~/Projects/gazebo/worlds

echo "Launching Gazebo with optimizations:"
echo "  - GPU: NVIDIA RTX 5070 Ti (forced)"
echo "  - Multi-threading: 8 threads"
echo "  - Physics: 250 Hz update rate"
echo ""

nice -n -10 gazebo --verbose iris_arducopter_cmac.world
