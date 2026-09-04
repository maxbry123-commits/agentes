#!/usr/bin/env python3
import os
import sys
import glob
import yaml
import re

def generate_scale_files(source_dir):
    """
    Generate scaled YAML files based on original files in source_dir.
    Creates scale_1k, scale_3k, and scale_10k folders with scaled versions.
    
    Args:
        source_dir: Directory containing original YAML files
    """
    # Define scales
    scales = [
        {"name": "1000", "display": "1k", "samples": 1000},
        {"name": "3160", "display": "3k", "samples": 3160},
        {"name": "10000", "display": "10k", "samples": 10000}
    ]
    
    # Ensure source directory exists and ends with a slash
    if not os.path.exists(source_dir):
        print(f"Error: Source directory {source_dir} does not exist")
        return
    
    source_dir = os.path.normpath(source_dir) + os.sep
    
    # Find all YAML files in the source directory
    yaml_files = glob.glob(os.path.join(source_dir, "*.yaml"))
    
    if not yaml_files:
        print(f"No YAML files found in {source_dir}")
        return
    
    # Create scale directories if they don't exist
    for scale in scales:
        scale_dir = os.path.join(source_dir, f"scale_{scale['name']}")
        os.makedirs(scale_dir, exist_ok=True)
    
    # Process each YAML file
    for yaml_file in yaml_files:
        filename = os.path.basename(yaml_file)
        base_name = os.path.splitext(filename)[0]
        
        # Skip if this is already a scale file (has _1k, _3k, _10k suffix)
        if re.search(r'_(1k|3k|10k)$', base_name):
            continue
        
        # Create a scaled version for each scale
        for scale in scales:
            scale_dir = os.path.join(source_dir, f"scale_{scale['name']}")
            scale_filename = f"{base_name}_{scale['display']}.yaml"
            scale_file_path = os.path.join(scale_dir, scale_filename)
            
            # Create the content for the scaled YAML file
            content = {
                "operators": [
                    {
                        "id": "load_preexisting",
                        "config": {
                            "type": "load_preexisting",
                            "framework_name": base_name
                        }
                    },
                    {
                        "id": "sample_dataset",
                        "config": {
                            "type": "function",
                            "function": "data_strategies.commons.uniform_sample_fixed",
                            "function_config": {
                                "num_samples": scale['samples']
                            }
                        },
                        "input_ids": ["load_hf"]
                    }
                ]
            }
            
            # Write the content to the scale file
            with open(scale_file_path, 'w') as f:
                yaml.dump(content, f, default_flow_style=False, sort_keys=False)
            
            print(f"Created {scale_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scale_generator.py <source_directory>")
        sys.exit(1)
    
    # Handle relative paths - assuming we're running from dcft/data_strategies
    source_dir = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # If path doesn't start with / or ./, assume it's relative to data_strategies dir
    if not source_dir.startswith('/') and not source_dir.startswith('./'):
        source_dir = os.path.join(script_dir, source_dir)
    
    generate_scale_files(source_dir)
    print("Scale files generation complete!")