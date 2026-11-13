import argparse
import json
import neptune
import dotenv
import logging
from docker_setup_old import *
dotenv.load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help='Path to config file', required=True)
parser.add_argument('-k', '--keep-running', action='store_true', help="Don't stop the attackbox after exiting")
args = parser.parse_args()
with open(args.config, 'r') as file:
	config = json.load(file)

run = neptune.init_run(project=config["neptune"]["project"])
logging.getLogger("neptune").setLevel(logging.ERROR)
run["config.json"].upload(args.config)
run["config"] = neptune.utils.stringify_unsupported(config)
llm_pipeline = create_llm_pipeline(model_id=config["llm"]["model_id"])
container = create_container(config=config)
failed_targets = []

for tgi,tg in enumerate(config["targets"]):
	print(f"[{tgi},0] Starting attack on: >{tg['target']}< (flag is {tg['flag']})\n")
	target_text = config["target_text"].format(target=tg["target"], info=tg["info"])
	summarized_history = ""; last_commands = []
	print_end_sep = "\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"

	if not "max_tries" in config:
		config["max_tries"] = 128
	for i in range(config["max_tries"]):
		succeeded = False; stop = False
		try:
			cmd_to_run = planner(
				summarized_history=target_text if summarized_history == "" else target_text+summarized_history+'\nLast commands:\n'+'\n'.join(last_commands),
				llm_pipeline=llm_pipeline,
				config=config,
			)
			print(f"[{tgi},{i}] Ran command '{cmd_to_run}':")
			command_output = container.exec_run(cmd_to_run).output.decode('utf-8').strip()
			if not command_output.strip():
				command_output = "*No output.*"
			print(command_output, end=print_end_sep)
			new_observation = f"{cmd_to_run}:\n{command_output}"
			last_commands.append(new_observation)
			if len(last_commands) > config["keep_commands"]:
				last_commands.pop(0)

			summarized_history = summarizer(
				summarized_history=summarized_history,
				new_observation=new_observation,
				llm_pipeline=llm_pipeline,
				config=config,
			)
			if tg["flag"] in summarized_history:
				succeeded = True
				print(f"[{tgi},{i}] Pwned target ({tg['target']}) with {cmd_to_run} (found the flag {tg['flag']} in summary)", end=print_end_sep)
				break
			print(f"[{tgi},{i}] Current summary:\n{summarized_history}", end=print_end_sep)
			run["summarized_history"].log(summarized_history + print_end_sep)
			run["last_commands"].log('\n'.join(last_commands) + print_end_sep)

		except KeyboardInterrupt:
			print(f"[{tgi},{i}] Quit requested by user, shutting down", end=print_end_sep)
			stop = True; break
	if not succeeded:
		failed_targets.append(tgi)
		print(f"[{tgi},{i}] Failed to pwn target ({tg['target']}).", end=print_end_sep)
	if stop:
		break

run["failed_targets"] = neptune.utils.stringify_unsupported(failed_targets)
print(f"Run finished. {tgi+1-len(failed_targets)}/{tgi+1} targets pwned ({round((tgi+1-len(failed_targets))/(tgi+1)*100,2)}%).\nFailed targets: {failed_targets}")

if not args.keep_running:
	container.stop() # maybe don't delete it, cause it takes a while to re-create