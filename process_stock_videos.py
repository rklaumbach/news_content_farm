import os
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import crop

# For downloaded videos from pexels.com in raw_videos directory

def resize_crop_cut_video(video_path, output_path):
    try:
        video = VideoFileClip(video_path)
        width, height = video.size
        
        # Cut to the first 10 seconds
        video = video.subclip(0, min(10, video.duration))
        
        # Resize the video to fit the vertical HD dimensions
        if width > height:
            # Landscape video, resize height first
            new_height = 1920
            new_width = int(new_height * width / height)
        else:
            # Portrait video, resize width first
            new_width = 1080
            new_height = int(new_width * height / width)
        
        # Resize the video
        video = video.resize((new_width, new_height))
        
        # Crop the video to vertical HD (1080x1920)
        video = crop(video, width=1080, height=1920, x_center=new_width / 2, y_center=new_height / 2)
        
        # Save the processed video
        video.write_videofile(output_path, codec='libx264')
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")

def process_videos(raw_videos_dir, stock_videos_dir):
    for topic in os.listdir(raw_videos_dir):
        topic_raw_dir = os.path.join(raw_videos_dir, topic)
        topic_stock_dir = os.path.join(stock_videos_dir, topic)

        if not os.path.isdir(topic_raw_dir):
            continue

        os.makedirs(topic_stock_dir, exist_ok=True)

        for video_file in os.listdir(topic_raw_dir):
            video_path = os.path.join(topic_raw_dir, video_file)
            
            # Remove everything after the hyphen in the filename
            base_filename = os.path.splitext(video_file)[0]
            cleaned_filename = base_filename.split('-')[0].strip() + ".mp4"
            
            output_path = os.path.join(topic_stock_dir, cleaned_filename)

            if os.path.isfile(video_path):
                resize_crop_cut_video(video_path, output_path)

if __name__ == "__main__":
    raw_videos_dir = 'raw_videos'
    stock_videos_dir = 'stock_videos'

    process_videos(raw_videos_dir, stock_videos_dir)
