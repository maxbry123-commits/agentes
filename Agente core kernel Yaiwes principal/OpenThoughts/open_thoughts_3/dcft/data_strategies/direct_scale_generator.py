#!/usr/bin/env python3
import os
import re
import argparse
from datasets import load_dataset

def get_scales(max_scale=None, min_scale=None):
    scales = [
        {"display": "0.3k", "samples": 316},
        {"display": "1k", "samples": 1000},
        {"display": "3k", "samples": 3160},
        {"display": "10k", "samples": 10000},
        {"display": "30k", "samples": 31600},
        {"display": "100k", "samples": 100000},
        {"display": "300k", "samples": 316000},
        {"display": "1000k", "samples": 1000000},
        {"display": "3000k", "samples": 3160000},
    ]
    
    valid_display_values = [s["display"] for s in scales]
    
    # Filter scales based on min_scale if provided
    if min_scale:
        if min_scale not in valid_display_values:
            print(f"Error: Invalid min_scale '{min_scale}'. Valid options are: {', '.join(valid_display_values)}")
            return None
            
        start_idx = valid_display_values.index(min_scale)
        scales = scales[start_idx:]
        valid_display_values = valid_display_values[start_idx:]
    
    # Filter scales based on max_scale if provided
    if max_scale:
        if max_scale not in valid_display_values:
            print(f"Error: Invalid max_scale '{max_scale}'. Valid options are: {', '.join(valid_display_values)}")
            return None
            
        filtered_scales = []
        for scale in scales:
            filtered_scales.append(scale)
            if scale["display"] == max_scale:
                break
        scales = filtered_scales
    
    return scales

def process_hf_dataset(hf_repo, max_scale=None, min_scale=None):
    scales = get_scales(max_scale, min_scale)
    if scales is None:
        return
    
    # Get max samples needed for validation
    max_samples = scales[-1]["samples"]
    
    # Get base name for target repos
    if "/" in hf_repo:
        org, base_name = hf_repo.split("/", 1)
    else:
        org = "mlfoundations-dev"
        base_name = hf_repo
    
    # Skip if this is already a scale file (has _0.3k, _1k, _3k, etc suffix)
    if re.search(r'_(0\.3k|1k|3k|10k|30k|100k|300k|1000k|3000k)$', base_name):
        print(f"Error: Source repo '{base_name}' appears to be a scaled dataset already")
        return
    
    print(f"Processing {hf_repo}...")
    
    # Load the dataset from HF Hub
    try:
        print(f"  Loading dataset from {hf_repo}")
        ds = load_dataset(hf_repo, split="train")
        
        # Check if dataset has enough samples for the max_scale
        if len(ds) < max_samples:
            raise ValueError(f"Dataset only has {len(ds)} samples, but {max_samples} are needed for scale {max_scale}")
        
        # Create a scaled version for each scale
        for scale in scales:
            target_repo = f"{org}/{base_name}_{scale['display']}"
            print(f" Downsampling to {scale['samples']} samples and pushing to {target_repo}")
            
            # Shuffle (different every time) and take the required number of samples
            shuffled_ds = ds.shuffle()
            downsampled_ds = shuffled_ds.take(scale['samples'])
            
            # Push to hub
            downsampled_ds.push_to_hub(target_repo)
            print(f"  Successfully pushed {len(downsampled_ds)} samples to {target_repo}")
            
    except Exception as e:
        print(f"Error processing {hf_repo}: {str(e)}")
        raise

def generate_scale_datasets(source_dir, max_scale=None, min_scale=None):
    scales = get_scales(max_scale, min_scale)
    if scales is None:
        return
    
    # Get max samples needed for validation
    max_samples = scales[-1]["samples"]
    
    # Ensure source directory exists and ends with a slash
    if not os.path.exists(source_dir):
        print(f"Error: Source directory {source_dir} does not exist")
        return
    
    source_dir = os.path.normpath(source_dir) + os.sep
    
    # Find all YAML files in the source directory and its subdirectories
    yaml_files = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".yaml"):
                yaml_files.append(os.path.join(root, file))
    
    if not yaml_files:
        print(f"No YAML files found in {source_dir} or its subdirectories")
        return
    
    # Process each YAML file
    for yaml_file in yaml_files:
        filename = os.path.basename(yaml_file)
        base_name = os.path.splitext(filename)[0]
        
        # Skip if this is already a scale file (has _0.3k, _1k, _3k, etc suffix)
        if re.search(r'_(0\.3k|1k|3k|10k|30k|100k|300k|1000k|3000k)$', base_name):
            continue
        
        print(f"Processing {base_name}...")
        
        # Load the dataset from HF Hub
        try:
            source_repo = f"mlfoundations-dev/{base_name}"
            print(f"  Loading dataset from {source_repo}")
            ds = load_dataset(source_repo, split="train")
            
            # Check if dataset has enough samples for the max_scale
            if max_scale and len(ds) < max_samples:
                raise ValueError(f"Dataset only has {len(ds)} samples, but {max_samples} are needed for scale {max_scale}")
            
            # Create a scaled version for each scale
            for scale in scales:
                target_repo = f"mlfoundations-dev/{base_name}_{scale['display']}"
                print(f" Downsampling to {scale['samples']} samples and pushing to {target_repo}")
                
                # Shuffle (different every time) and take the required number of samples
                shuffled_ds = ds.shuffle()
                downsampled_ds = shuffled_ds.take(scale['samples'])
                
                # Push to hub
                downsampled_ds.push_to_hub(target_repo)
                print(f"  Successfully pushed {len(downsampled_ds)} samples to {target_repo}")
                
        except Exception as e:
            print(f"Error processing {base_name}: {str(e)}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate scaled datasets from source YAML files or Hugging Face dataset")
    parser.add_argument("source", help="Directory containing source YAML files or HF dataset if --hf is specified")
    parser.add_argument("--max-scale", default="10k", help="Maximum scale to generate (1k, 3k, 10k, 30k, 100k, 300k, 1000k, or 3000k)")
    parser.add_argument("--min-scale", default=None, help="Minimum scale to generate (1k, 3k, 10k, 30k, 100k, 300k, 1000k, or 3000k)")
    parser.add_argument("--hf", action="store_true", help="Treat source as a Hugging Face dataset ID instead of directory")
    args = parser.parse_args()
    
    if args.hf:
        # Process a single HF dataset
        process_hf_dataset(args.source, args.max_scale, args.min_scale)
    else:
        # Process a directory of YAML files
        source_dir = args.source
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # If path doesn't start with / or ./, assume it's relative to data_strategies dir
        if not source_dir.startswith('/') and not source_dir.startswith('./'):
            source_dir = os.path.join(script_dir, source_dir)
        
        generate_scale_datasets(source_dir, args.max_scale, args.min_scale)
    
    print("Scale datasets generation complete!")