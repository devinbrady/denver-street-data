# ffmpeg.sh

# Run this command in the terminal to turn the PNGs into a video, with title card and initial map

ffmpeg \
-loop 1 \
-t 3 \
-framerate 12 \
-i video_downtown/downtown_title_card.png \
-loop 1 \
-t 3 \
-framerate 12 \
-i video_downtown/initial_map.png \
-framerate 12 \
-i video_downtown/frame_%4d.png \
-filter_complex '[0:0] [1:0] [2:0] concat=n=3:v=1:a=0' \
-c:v h264 \
-r 30 \
-s 1920x1080 \
video_downtown/crashes.mp4





# ffmpeg -framerate 12 -i video_downtown/frame_%4d.png -c:v h264 -r 30 -s 1920x1080 video_downtown/crashes.mp4