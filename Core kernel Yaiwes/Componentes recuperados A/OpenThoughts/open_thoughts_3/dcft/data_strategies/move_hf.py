#!/usr/bin/env python
"""
Script to move Hugging Face repositories with a specified prefix.
Example usage: 
    python move_hf.py --prefix "fig1_all_" --org "mlfoundations-dev" --type dataset
    python move_hf.py --prefix "fig1_all_" --org "mlfoundations-dev" --type model
    python move_hf.py --prefix "fig1_all_" --replace-prefix "figure1_" --org "mlfoundations-dev" --type dataset
"""

import argparse
import os
from huggingface_hub import move_repo, list_models, list_datasets, login

def move_repositories(prefix, org, repo_type="dataset", replace_prefix=None, dry_run=False):
    """
    Move repositories with a specified prefix to new locations.
    
    Args:
        prefix (str): The prefix to match in repository names
        org (str): Organization name on Hugging Face
        repo_type (str): Type of repository ('dataset' or 'model')
        replace_prefix (str, optional): If provided, replace the old prefix with this new prefix
                                       instead of removing it completely
        dry_run (bool): If True, only print what would be moved without actually moving
    """
    if repo_type == "dataset":
        repos = list_datasets(author=org)
    elif repo_type == "model":
        repos = list_models(author=org)
    else:
        raise ValueError("Repository type must be 'dataset' or 'model'")
    
    total_count = 0
    success_count = 0
    
    for repo in repos:
        repo_id = repo.id if repo_type == "dataset" else repo.modelId
        repo_name = repo_id.split('/')[-1]
        
        if repo_name.startswith(prefix):
            # Create the new name - either replace the prefix or remove it
            if replace_prefix is not None:
                new_name = replace_prefix + repo_name[len(prefix):]
            else:
                new_name = repo_name[len(prefix):]
                
            from_id = f"{org}/{repo_name}"
            to_id = f"{org}/{new_name}"
            
            print(f"Moving {repo_type}: {from_id} -> {to_id}")
            total_count += 1
            
            if not dry_run:
                try:
                    move_repo(from_id=from_id, to_id=to_id, repo_type=repo_type)
                    print(f"✅ Successfully moved {from_id} to {to_id}")
                    success_count += 1
                except Exception as e:
                    print(f"❌ Failed to move {from_id}: {str(e)}")
                    # If it's a conflict error (409), provide a link to the conflicting resource
                    if "409 Client Error: Conflict" in str(e):
                        print(f"⚠️  Conflicting repository exists at: https://huggingface.co/{to_id}")
            else:
                success_count += 1
    
    print(f"\nFound {total_count} {repo_type}s with prefix '{prefix}'")
    if dry_run:
        print("Dry run completed. No repositories were actually moved.")
    else:
        print(f"Successfully moved {success_count} out of {total_count} {repo_type}s.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Move Hugging Face repositories with a specified prefix")
    parser.add_argument("--prefix", required=True, help="Prefix to match in repository names (e.g., 'fig1_all_')")
    parser.add_argument("--replace-prefix", help="Replace the old prefix with this new prefix instead of removing it")
    parser.add_argument("--org", default="mlfoundations-dev", help="Organization name on Hugging Face")
    parser.add_argument("--type", default="dataset", choices=["dataset", "model"], 
                      help="Type of repository to move ('dataset' or 'model')")
    parser.add_argument("--token", help="Hugging Face API token (alternatively, set the HF_TOKEN environment variable)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be moved without moving anything")
    parser.add_argument("--list-only", action="store_true", help="Just list repositories with the prefix without moving")
    
    args = parser.parse_args()
    
    # Authenticate with Hugging Face
    token = args.token or os.environ.get("HF_TOKEN")
    if token:
        print("Authenticating with Hugging Face...")
        login(token=token)
    else:
        print("Warning: No Hugging Face token provided. You may encounter authentication errors.")
        print("Set the HF_TOKEN environment variable or provide --token.")
    
    # Just list repositories if requested
    if args.list_only:
        org = args.org
        prefix = args.prefix
        repo_type = args.type
        replace_prefix = args.replace_prefix
        
        print(f"Listing {repo_type}s in '{org}' with prefix '{prefix}':")
        
        if repo_type == "dataset":
            repos = list_datasets(author=org)
        else:
            repos = list_models(author=org)
            
        count = 0
        for repo in repos:
            repo_id = repo.id if repo_type == "dataset" else repo.modelId
            repo_name = repo_id.split('/')[-1]
            
            if repo_name.startswith(prefix):
                count += 1
                if replace_prefix is not None:
                    new_name = replace_prefix + repo_name[len(prefix):]
                else:
                    new_name = repo_name[len(prefix):]
                print(f"{repo_type.capitalize()}: {repo_id} -> {org}/{new_name}")
        
        print(f"\nFound {count} {repo_type}s with prefix '{prefix}'")
    else:
        # Move the repositories
        operation = "replacing" if args.replace_prefix else "removing"
        print(f"Looking for {args.type}s in '{args.org}' with prefix '{args.prefix}' ({operation} prefix)...")
        move_repositories(args.prefix, args.org, args.type, args.replace_prefix, args.dry_run)