#!/bin/bash

# ============================================================================
# Image to Video Converter
# ============================================================================
# Converts images to videos by displaying the image for a configurable duration
# followed by a black screen for a configurable duration.
#
# Requirements: FFmpeg must be installed
# Usage: ./convert_images_to_videos.sh
# ============================================================================

# Configuration variables
IMAGE_DURATION=2          # Duration to display the image (seconds)
BLACK_DURATION=2          # Duration to display black screen (seconds)
INPUT_FOLDER="./images"   # Path to folder containing input images
OUTPUT_FOLDER="./videos"  # Path to folder for output videos

# Video encoding settings
FPS=30                    # Frames per second
VIDEO_CODEC="libx264"     # Video codec
PIXEL_FORMAT="yuv420p"    # Pixel format (yuv420p for compatibility)

# ============================================================================
# Script execution (do not modify below unless you know what you're doing)
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Image to Video Converter"
    echo "========================"
    echo "Converts images to videos with configurable display times."
    echo ""
    echo "Configuration (edit script to change):"
    echo "  IMAGE_DURATION: ${IMAGE_DURATION}s"
    echo "  BLACK_DURATION: ${BLACK_DURATION}s"
    echo "  INPUT_FOLDER:   ${INPUT_FOLDER}"
    echo "  OUTPUT_FOLDER:  ${OUTPUT_FOLDER}"
    echo ""
}

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: FFmpeg is not installed.${NC}"
    echo "Please install FFmpeg first:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    exit 1
fi

# Display configuration
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Image to Video Converter${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Image display time: ${GREEN}${IMAGE_DURATION}s${NC}"
echo -e "Black screen time:  ${GREEN}${BLACK_DURATION}s${NC}"
echo -e "Input folder:       ${GREEN}${INPUT_FOLDER}${NC}"
echo -e "Output folder:      ${GREEN}${OUTPUT_FOLDER}${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if input folder exists
if [ ! -d "$INPUT_FOLDER" ]; then
    echo -e "${RED}Error: Input folder '${INPUT_FOLDER}' does not exist.${NC}"
    exit 1
fi

# Create output folder if it doesn't exist
mkdir -p "$OUTPUT_FOLDER"

# Count total images
TOTAL_IMAGES=$(find "$INPUT_FOLDER" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.bmp" -o -iname "*.tiff" -o -iname "*.webp" \) | wc -l)

if [ "$TOTAL_IMAGES" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No image files found in '${INPUT_FOLDER}'${NC}"
    echo "Supported formats: JPG, JPEG, PNG, BMP, TIFF, WEBP"
    exit 0
fi

echo -e "Found ${GREEN}${TOTAL_IMAGES}${NC} images to convert"
echo ""

# Counter for progress
CURRENT=0
SUCCESSFUL=0
FAILED=0

# Calculate total duration
TOTAL_DURATION=$((IMAGE_DURATION + BLACK_DURATION))

# Build array of image files (to avoid subshell issues with pipe)
mapfile -t image_files < <(find "$INPUT_FOLDER" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.bmp" -o -iname "*.tiff" -o -iname "*.webp" \) | sort)

# Process each image file
for image_path in "${image_files[@]}"; do
    CURRENT=$((CURRENT + 1))

    # Get filename without path
    filename=$(basename "$image_path")

    # Get filename without extension
    filename_no_ext="${filename%.*}"

    # Output video path
    output_path="${OUTPUT_FOLDER}/${filename_no_ext}.mp4"

    echo -e "[${CURRENT}/${TOTAL_IMAGES}] Processing: ${BLUE}${filename}${NC}"

    # Check if file actually exists and is readable
    if [ ! -r "$image_path" ]; then
        echo -e "  ${RED}✗ Cannot read file: $image_path${NC}"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Create temporary black image (1x1 pixel, will be scaled)
    temp_black=$(mktemp /tmp/black_XXXXXX.png)
    convert -size 1x1 xc:black "$temp_black" 2>/dev/null || {
        # Fallback if ImageMagick is not available
        ffmpeg -f lavfi -i color=c=black:s=1920x1080:d=1 -frames:v 1 "$temp_black" -y -loglevel quiet 2>&1
    }

    # Create video using FFmpeg
    # Step 1: Create video from image
    # Step 2: Create video from black screen
    # Step 3: Concatenate them

    # Create temporary files for segments
    temp_image_video=$(mktemp /tmp/img_XXXXXX.mp4)
    temp_black_video=$(mktemp /tmp/blk_XXXXXX.mp4)
    temp_concat_list=$(mktemp /tmp/concat_XXXXXX.txt)

    # Convert image to video segment
    error_msg=$(ffmpeg -loop 1 -i "$image_path" -t "$IMAGE_DURATION" -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" -c:v "$VIDEO_CODEC" -r "$FPS" -pix_fmt "$PIXEL_FORMAT" "$temp_image_video" -y 2>&1)

    if [ $? -ne 0 ]; then
        echo -e "  ${RED}✗ Failed to create image video segment${NC}"
        echo -e "  ${YELLOW}Image path: $image_path${NC}"
        echo -e "  ${YELLOW}Error: $(echo "$error_msg" | tail -n 3)${NC}"
        FAILED=$((FAILED + 1))
        rm -f "$temp_black" "$temp_image_video" "$temp_black_video" "$temp_concat_list"
        continue
    fi

    # Convert black screen to video segment
    error_msg=$(ffmpeg -loop 1 -i "$temp_black" -t "$BLACK_DURATION" -vf "scale=1920:1080" -c:v "$VIDEO_CODEC" -r "$FPS" -pix_fmt "$PIXEL_FORMAT" "$temp_black_video" -y 2>&1)

    if [ $? -ne 0 ]; then
        echo -e "  ${RED}✗ Failed to create black screen segment${NC}"
        echo -e "  ${YELLOW}Error: $(echo "$error_msg" | tail -n 3)${NC}"
        FAILED=$((FAILED + 1))
        rm -f "$temp_black" "$temp_image_video" "$temp_black_video" "$temp_concat_list"
        continue
    fi

    # Create concatenation list with absolute paths (safer for special characters)
    temp_image_video_abs=$(realpath "$temp_image_video")
    temp_black_video_abs=$(realpath "$temp_black_video")
    echo "file '$temp_image_video_abs'" > "$temp_concat_list"
    echo "file '$temp_black_video_abs'" >> "$temp_concat_list"

    # Concatenate the two segments
    error_msg=$(ffmpeg -f concat -safe 0 -i "$temp_concat_list" -c copy "$output_path" -y 2>&1)

    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Created: ${filename_no_ext}.mp4${NC}"
        SUCCESSFUL=$((SUCCESSFUL + 1))
    else
        echo -e "  ${RED}✗ Failed to concatenate segments${NC}"
        echo -e "  ${YELLOW}Error: $(echo "$error_msg" | tail -n 3)${NC}"
        FAILED=$((FAILED + 1))
    fi

    # Clean up temporary files
    rm -f "$temp_black" "$temp_image_video" "$temp_black_video" "$temp_concat_list"

done

# Summary
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Conversion Complete${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Total images:  ${TOTAL_IMAGES}"
echo -e "Successful:    ${GREEN}${SUCCESSFUL}${NC}"
echo -e "Failed:        ${RED}${FAILED}${NC}"
echo -e "Output folder: ${GREEN}${OUTPUT_FOLDER}${NC}"
echo -e "${BLUE}================================${NC}"
