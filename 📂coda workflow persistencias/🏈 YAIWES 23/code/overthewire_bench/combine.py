import json

# List of tuples containing the filename and corresponding wargame name
files = [
	('bandit_solved.json', 'bandit'),
	('krypton_solved.json', 'krypton'),
	('leviathan_solved.json', 'leviathan'),
	('natas_solved.json', 'natas'),
]

combined_data = {}

for filename, wargame_name in files:
	with open(filename, 'r') as f:
		challenges = json.load(f)
		challenge_id = 1  # Start challenge ID from 1 for each wargame
		for challenge in challenges:
			# Create a unique key for the challenge
			challenge_key = f"{wargame_name}_{challenge_id}"
			challenge_id += 1
			# Add the 'wargame' field
			challenge['wargame'] = wargame_name
			# Optionally remove or adjust the 'id' field
			# Add the challenge to the combined dictionary
			combined_data[challenge_key] = challenge

# Write the combined data to a new JSON file
with open('combined_solved.json', 'w') as outfile:
	json.dump(combined_data, outfile, indent='\t')
