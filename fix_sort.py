import os

def rename_videos_to_match_input(directory, prefix, extension):
    # Hardcoded mapping for up to 20 files
    mapping = {
        1: 1, 2: 10, 3: 11, 4: 12, 5: 13,
        6: 14, 7: 15, 8: 16, 9: 17, 10: 18,
        11: 19, 12: 20, 13: 2, 14: 3, 15: 4,
        16: 5, 17: 6, 18: 7, 19: 8, 20: 9
    }
    
    # List all video files with the current prefix and extension
    current_files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith(extension)]
    
    # Print the mapping for verification
    print("Mapping (Current Index -> Correct Index):")
    for k, v in mapping.items():
        print(f"{k} -> {v}")
    
    # Step 1: Rename files to temporary names to avoid collisions
    for i, filename in enumerate(current_files, 1):
        temp_name = f"temp_{i}{extension}"
        src = os.path.join(directory, filename)
        temp_dst = os.path.join(directory, temp_name)
        os.rename(src, temp_dst)
        print(f"Temporarily renamed {src} to {temp_dst}")
    
    # Step 2: Rename temporary files to the final names based on the mapping
    for current_index, correct_index in mapping.items():
        temp_src = os.path.join(directory, f"temp_{current_index}{extension}")
        final_dst = os.path.join(directory, f"{prefix}_{correct_index}{extension}")
        os.rename(temp_src, final_dst)
        print(f"Renamed {temp_src} to {final_dst}")

# Usage
directory = 'output/2024-05-27/technology/video'
prefix = 'video_file'
extension = '.mp4'

rename_videos_to_match_input(directory, prefix, extension)
